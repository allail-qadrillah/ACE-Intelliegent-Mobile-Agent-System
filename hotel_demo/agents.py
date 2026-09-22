"""Agen: static agents, orchestrator, dan mobile investigator.

Setiap agen adalah class Python kecil dengan ``handle(message, sim)``. Keputusan
berbasis rules/state machine; tidak ada LLM.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence

from . import policy
from .models import (
    Action,
    AgentPhase,
    AgentRuntimeStatus,
    EventType,
    Message,
    MessageKind,
    NodeId,
)

# Capability ditentukan konfigurasi runtime berdasarkan jenis agen terdaftar,
# bukan dipercayai dari checkpoint/payload.
CAPABILITIES: Dict[str, tuple] = {
    "scenario_scout": (),
    "orchestrator": (),
    "reservation": ("read_reservation", "commit_room_change"),
    "billing": ("read_folio",),
    "concierge": ("read_faq",),
    "operations": ("inspect_readiness", "create_ticket", "update_ticket"),
    "investigator": ("inspect_readiness",),
}

DATA_CAPABILITIES: Dict[str, set] = {
    NodeId.FRONT_OFFICE.value: {"reservation", "folio", "faq"},
    NodeId.OPERATIONS.value: {"readiness", "ticket"},
}


def evaluate_candidates(
    candidate_snapshots: Sequence[Dict[str, Any]],
    readiness_records: Sequence[Dict[str, Any]],
    constraints: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Kernel murni yang dipakai jalur mobile maupun baseline statis."""
    readiness_by_room = {record["room_id"]: record for record in readiness_records}
    requested_type = constraints.get("room_type")
    max_rate = int(constraints.get("max_rate", 0))
    results: List[Dict[str, Any]] = []

    for candidate in candidate_snapshots:
        room_id = candidate["room_id"]
        readiness = readiness_by_room.get(room_id)
        clean = bool(readiness) and readiness.get("cleanliness") == "clean"
        blocked = bool(readiness) and bool(readiness.get("maintenance_blocked"))
        is_ready = clean and not blocked
        type_ok = candidate.get("room_type") == requested_type
        rate_ok = int(candidate.get("nightly_rate", 0)) <= max_rate
        is_routine_eligible = is_ready and type_ok and rate_ok

        reason_codes: List[str] = []
        if not clean:
            reason_codes.append("DIRTY")
        if blocked:
            reason_codes.append("MAINTENANCE_BLOCKED")
        if is_ready and not type_ok:
            reason_codes.append("UPGRADE_REQUIRES_HUMAN")
        if is_ready and type_ok and not rate_ok:
            reason_codes.append("RATE_REQUIRES_HUMAN")
        if is_routine_eligible:
            reason_codes.append("READY_EQUAL_ROOM")

        rate_delta = int(candidate.get("nightly_rate", 0)) - int(
            constraints.get("reservation_rate", max_rate)
        )
        results.append(
            {
                "room_id": room_id,
                "room_type": candidate.get("room_type"),
                "nightly_rate": candidate.get("nightly_rate"),
                "room_version": candidate.get("room_version"),
                "evidence_version": None if readiness is None else readiness.get("evidence_version"),
                "is_ready": is_ready,
                "is_routine_eligible": is_routine_eligible,
                "reason_codes": reason_codes,
                "rate_delta": rate_delta,
            }
        )
    return results


class BaseAgent:
    capability_key = ""

    def __init__(self, agent_id: str, node_id: str, case_id: Optional[str] = None) -> None:
        self.agent_id = agent_id
        self.node_id = node_id
        self.status = AgentRuntimeStatus.ACTIVE.value
        self.phase = AgentPhase.CREATED.value
        self.case_id = case_id
        self.last_action: Optional[str] = None

    @property
    def agent_type(self) -> str:
        return "static"

    @property
    def capabilities(self) -> tuple:
        return CAPABILITIES.get(self.capability_key, ())

    def state_snapshot(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "node_id": self.node_id,
            "status": self.status,
            "phase": self.phase,
            "case_id": self.case_id,
            "last_action": self.last_action,
            "capabilities": list(self.capabilities),
        }

    def handle(self, message: Message, sim: Any) -> None:  # pragma: no cover - abstract
        raise NotImplementedError


class ScenarioScoutAgent(BaseAgent):
    """Scout: membentuk request terstruktur dari fixture (tanpa NLP)."""

    capability_key = "scenario_scout"

    def __init__(self, node_id: str = NodeId.FRONT_OFFICE.value) -> None:
        super().__init__("scenario_scout", node_id)

    def build_start_message(self, scenario: Dict[str, Any], run_id: str) -> Message:
        self.last_action = Action.START_CASE.value
        return Message(
            message_id="MSG-000",
            run_id=run_id,
            case_id="CASE-001",
            sender=self.agent_id,
            receiver="orchestrator",
            source_node=self.node_id,
            destination_node=self.node_id,
            kind=MessageKind.REQUEST.value,
            action=Action.START_CASE.value,
            correlation_id="TASK-TRIAGE-001",
            payload={
                "scenario_id": scenario["id"],
                "intent": scenario["intent"],
                "flow": scenario["flow"],
                "guest_message": scenario["guest_message"],
                "features": scenario["features"],
                "flags": scenario.get("flags", {}),
                "include_upgrade_alternatives": scenario.get("include_upgrade_alternatives", False),
                "constraints": scenario.get("constraints", {}),
                "faq_key": scenario.get("faq_key"),
            },
        )

    def handle(self, message: Message, sim: Any) -> None:  # pragma: no cover - scout is a sender
        sim.emit(
            EventType.HANDLER_ERROR.value,
            agent_id=self.agent_id,
            node_id=self.node_id,
            details={"reason": "SCOUT_IS_SENDER_ONLY"},
        )


class ReservationAgent(BaseAgent):
    capability_key = "reservation"

    def __init__(self, node_id: str = NodeId.FRONT_OFFICE.value) -> None:
        super().__init__("reservation", node_id)

    def handle(self, message: Message, sim: Any) -> None:
        self.last_action = message.action
        if message.action == Action.FIND_ROOM_CANDIDATES.value:
            self._find_candidates(message, sim)
        elif message.action == Action.COMMIT_ROOM_CHANGE.value:
            self._commit(message, sim)
        else:
            sim.structured_failure(message, "UNKNOWN_ACTION", "Aksi tidak dikenal Reservation Agent.")

    def _find_candidates(self, message: Message, sim: Any) -> None:
        reservation_id = message.payload.get("reservation_id")
        include_upgrade = bool(message.payload.get("include_upgrade_alternatives"))
        result = sim.node_repo(self.node_id).find_candidates(reservation_id, include_upgrade)
        if not result["ok"]:
            sim.tool_refused(self, message, result["error"])
            sim.enqueue(
                sim.make_message(
                    sender=self.agent_id,
                    receiver=message.sender,
                    action=Action.CANDIDATES_FOUND.value,
                    kind=MessageKind.FAILURE.value,
                    payload=result,
                    correlation_id=message.correlation_id,
                )
            )
            return
        sim.emit(
            EventType.TOOL_SUCCEEDED.value,
            agent_id=self.agent_id,
            node_id=self.node_id,
            details={"tool": "find_candidates", "count": len(result["candidates"])},
        )
        sim.enqueue(
            sim.make_message(
                sender=self.agent_id,
                receiver=message.sender,
                action=Action.CANDIDATES_FOUND.value,
                payload={
                    "candidates": result["candidates"],
                    "reservation": result["reservation"],
                    "include_upgrade_alternatives": include_upgrade,
                },
                correlation_id=message.correlation_id,
            )
        )

    def _commit(self, message: Message, sim: Any) -> None:
        payload = message.payload
        result = sim.node_repo(self.node_id).commit_room_change(
            reservation_id=payload["reservation_id"],
            target_room_id=payload["target_room_id"],
            case_id=payload["case_id"],
            expected_versions=payload["expected_versions"],
            fresh_readiness=payload.get("fresh_readiness"),
            consent=payload.get("consent"),
            operation_key=payload["operation_key"],
            policy_decision=payload.get("policy_decision"),
            case=payload.get("case"),
            recheck_correlation_id=payload.get("recheck_correlation_id"),
            expected_recheck_correlation=payload.get("expected_recheck_correlation"),
        )
        if result["ok"]:
            sim.emit(
                EventType.TOOL_SUCCEEDED.value,
                agent_id=self.agent_id,
                node_id=self.node_id,
                details={"tool": "commit_room_change", "result": result.get("result")},
            )
        else:
            sim.emit(
                EventType.TOOL_REFUSED.value,
                agent_id=self.agent_id,
                node_id=self.node_id,
                reason_codes=[result["error"]["code"]],
                details={"tool": "commit_room_change", "error": result["error"]},
            )
        sim.enqueue(
            sim.make_message(
                sender=self.agent_id,
                receiver=message.sender,
                action=Action.ROOM_CHANGE_RESULT.value,
                kind=MessageKind.INFORM.value if result["ok"] else MessageKind.FAILURE.value,
                payload=result,
                correlation_id=message.correlation_id,
            )
        )


class BillingAgent(BaseAgent):
    capability_key = "billing"

    def __init__(self, node_id: str = NodeId.FRONT_OFFICE.value) -> None:
        super().__init__("billing", node_id)

    def handle(self, message: Message, sim: Any) -> None:
        self.last_action = message.action
        if message.action != Action.GET_FOLIO.value:
            sim.structured_failure(message, "UNKNOWN_ACTION", "Aksi tidak dikenal Billing Agent.")
            return
        result = sim.node_repo(self.node_id).get_folio(message.payload.get("reservation_id"))
        if not result["ok"]:
            sim.tool_refused(self, message, result["error"])
        else:
            sim.emit(
                EventType.TOOL_SUCCEEDED.value,
                agent_id=self.agent_id,
                node_id=self.node_id,
                details={"tool": "get_folio", "total": result["total"]},
            )
        sim.enqueue(
            sim.make_message(
                sender=self.agent_id,
                receiver=message.sender,
                action=Action.FOLIO_RESULT.value,
                kind=MessageKind.INFORM.value if result["ok"] else MessageKind.FAILURE.value,
                payload=result,
                correlation_id=message.correlation_id,
            )
        )


class ConciergeAgent(BaseAgent):
    capability_key = "concierge"

    def __init__(self, node_id: str = NodeId.FRONT_OFFICE.value) -> None:
        super().__init__("concierge", node_id)

    def handle(self, message: Message, sim: Any) -> None:
        self.last_action = message.action
        if message.action != Action.GET_FAQ.value:
            sim.structured_failure(message, "UNKNOWN_ACTION", "Aksi tidak dikenal Concierge Agent.")
            return
        result = sim.node_repo(self.node_id).get_faq(message.payload.get("key"))
        if not result["ok"]:
            sim.tool_refused(self, message, result["error"])
        else:
            sim.emit(
                EventType.TOOL_SUCCEEDED.value,
                agent_id=self.agent_id,
                node_id=self.node_id,
                details={"tool": "get_faq", "key": result["key"]},
            )
        sim.enqueue(
            sim.make_message(
                sender=self.agent_id,
                receiver=message.sender,
                action=Action.FAQ_RESULT.value,
                kind=MessageKind.INFORM.value if result["ok"] else MessageKind.FAILURE.value,
                payload=result,
                correlation_id=message.correlation_id,
            )
        )


class OperationsAgent(BaseAgent):
    capability_key = "operations"

    def __init__(self, node_id: str = NodeId.OPERATIONS.value) -> None:
        super().__init__("operations", node_id)

    def handle(self, message: Message, sim: Any) -> None:
        self.last_action = message.action
        if message.action == Action.CREATE_TICKET.value:
            self._create_ticket(message, sim)
        elif message.action == Action.GET_READINESS.value:
            self._get_readiness(message, sim)
        elif message.action == Action.INSPECT_CANDIDATES.value:
            self._inspect_batch(message, sim)
        else:
            sim.structured_failure(message, "UNKNOWN_ACTION", "Aksi tidak dikenal Operations Agent.")

    def _create_ticket(self, message: Message, sim: Any) -> None:
        payload = message.payload
        result = sim.node_repo(self.node_id).create_ticket(
            case_id=payload["case_id"],
            room_id=payload["room_id"],
            department=payload["department"],
            description=payload["description"],
            operation_key=payload["operation_key"],
        )
        sim.emit(
            EventType.TOOL_SUCCEEDED.value,
            agent_id=self.agent_id,
            node_id=self.node_id,
            details={
                "tool": "create_ticket",
                "ticket_id": result["ticket"]["id"],
                "idempotent": result.get("idempotent", False),
            },
        )
        sim.enqueue(
            sim.make_message(
                sender=self.agent_id,
                receiver=message.sender,
                action=Action.TICKET_CREATED.value,
                payload=result,
                correlation_id=message.correlation_id,
            )
        )

    def _get_readiness(self, message: Message, sim: Any) -> None:
        room_ids = message.payload.get("room_ids", [])
        result = sim.read_local_readiness(self.agent_id, room_ids)
        if not result["ok"]:
            sim.tool_refused(self, message, result["error"])
        else:
            sim.emit(
                EventType.TOOL_SUCCEEDED.value,
                agent_id=self.agent_id,
                node_id=self.node_id,
                details={"tool": "get_readiness", "room_ids": list(room_ids)},
            )
        sim.enqueue(
            sim.make_message(
                sender=self.agent_id,
                receiver=message.sender,
                action=Action.READINESS_RESULT.value,
                kind=MessageKind.INFORM.value if result["ok"] else MessageKind.FAILURE.value,
                payload=result,
                correlation_id=message.correlation_id,
            )
        )

    def _inspect_batch(self, message: Message, sim: Any) -> None:
        """Baseline statis: kernel yang sama dijalankan di node tempat data berada."""
        caller = sim.agents.get(message.sender)
        if caller is None or "inspect_readiness" not in caller.capabilities:
            sim.tool_refused(
                self,
                message,
                {"code": "MISSING_CAPABILITY", "message": "Pemanggil tidak berhak inspeksi.", "details": {}},
            )
            sim.enqueue(
                sim.make_message(
                    sender=self.agent_id,
                    receiver=message.sender,
                    action=Action.INSPECTION_RESULT.value,
                    kind=MessageKind.FAILURE.value,
                    payload={
                        "ok": False,
                        "error": {
                            "code": "MISSING_CAPABILITY",
                            "message": "Pemanggil tidak berhak inspeksi.",
                            "details": {},
                        },
                    },
                    correlation_id=message.correlation_id,
                )
            )
            return

        candidates = message.payload.get("candidates", [])
        constraints = message.payload.get("constraints", {})
        room_ids = [candidate["room_id"] for candidate in candidates]
        readiness = sim.read_local_readiness(self.agent_id, room_ids)
        if not readiness["ok"]:
            sim.tool_refused(self, message, readiness["error"])
            sim.enqueue(
                sim.make_message(
                    sender=self.agent_id,
                    receiver=message.sender,
                    action=Action.INSPECTION_RESULT.value,
                    kind=MessageKind.FAILURE.value,
                    payload=readiness,
                    correlation_id=message.correlation_id,
                )
            )
            return

        results = evaluate_candidates(candidates, readiness["readiness"], constraints)
        sim.emit(
            EventType.LOCAL_INSPECTION_COMPLETED.value,
            agent_id=self.agent_id,
            node_id=self.node_id,
            details={"mode": "static_batch", "room_ids": room_ids},
        )
        sim.enqueue(
            sim.make_message(
                sender=self.agent_id,
                receiver=message.sender,
                action=Action.INSPECTION_RESULT.value,
                payload={"results": results, "mode": "static_batch"},
                correlation_id=message.correlation_id,
            )
        )


class OrchestratorAgent(BaseAgent):
    capability_key = "orchestrator"

    def __init__(self, node_id: str = NodeId.FRONT_OFFICE.value) -> None:
        super().__init__("orchestrator", node_id)

    def handle(self, message: Message, sim: Any) -> None:
        self.last_action = message.action
        handlers = {
            Action.START_CASE.value: self._start_case,
            Action.TICKET_CREATED.value: self._on_ticket_created,
            Action.CANDIDATES_FOUND.value: self._on_candidates_found,
            Action.INSPECTION_RESULT.value: self._on_inspection_result,
            Action.FOLIO_RESULT.value: self._on_folio_result,
            Action.FAQ_RESULT.value: self._on_faq_result,
            Action.GUEST_CONSENT.value: self._on_guest_consent,
            Action.READINESS_RESULT.value: self._on_readiness_result,
            Action.ROOM_CHANGE_RESULT.value: self._on_room_change_result,
        }
        handler = handlers.get(message.action)
        if handler is None:
            sim.structured_failure(message, "UNKNOWN_ACTION", "Aksi tidak dikenal Orchestrator.")
            return
        handler(message, sim)

    # --------------------------------------------------------------- triase
    def _start_case(self, message: Message, sim: Any) -> None:
        payload = message.payload
        features = payload["features"]
        flags = payload.get("flags", {})

        probability = float(sim.model.predict(features))
        sim.emit(
            EventType.MODEL_PREDICTED.value,
            agent_id=self.agent_id,
            node_id=self.node_id,
            details={
                "p_human": probability,
                "threshold": sim.threshold,
                "features": features,
                "model_recommends_human": probability >= sim.threshold,
            },
        )
        decision = policy.evaluate_case(flags, probability, sim.threshold)
        sim.emit(
            EventType.POLICY_EVALUATED.value,
            agent_id=self.agent_id,
            node_id=self.node_id,
            reason_codes=decision.reason_codes,
            details=decision.to_dict(),
        )

        case = sim.create_case(payload)
        sim.apply_policy_decision(decision)

        flow = case.flow
        if flow in ("room_change", "housekeeping"):
            if flow == "room_change":
                department = "MAINTENANCE"
                description = f"Perbaikan AC kamar {case.original_room_id}"
                suffix = "maintenance"
            else:
                department = "HOUSEKEEPING"
                description = f"Antar handuk ke kamar {case.original_room_id}"
                suffix = "housekeeping"
            sim.enqueue(
                sim.make_message(
                    sender=self.agent_id,
                    receiver="operations",
                    action=Action.CREATE_TICKET.value,
                    payload={
                        "case_id": case.case_id,
                        "room_id": case.original_room_id,
                        "department": department,
                        "description": description,
                        "operation_key": f"ticket:{case.case_id}:{suffix}",
                    },
                    correlation_id=f"TASK-TICKET-{case.case_id}",
                )
            )
        elif flow in ("billing_dispute", "billing_details"):
            sim.enqueue(
                sim.make_message(
                    sender=self.agent_id,
                    receiver="billing",
                    action=Action.GET_FOLIO.value,
                    payload={"reservation_id": case.reservation_id},
                    correlation_id=f"TASK-FOLIO-{case.case_id}",
                )
            )
        elif flow == "faq":
            sim.enqueue(
                sim.make_message(
                    sender=self.agent_id,
                    receiver="concierge",
                    action=Action.GET_FAQ.value,
                    payload={"key": payload.get("faq_key") or "check_in"},
                    correlation_id=f"TASK-FAQ-{case.case_id}",
                )
            )
        else:
            sim.set_case_status(
                sim.case.status,
                reason_codes=["UNKNOWN_FLOW"],
                event_details={"flow": flow},
            )

    def _on_ticket_created(self, message: Message, sim: Any) -> None:
        case = sim.case
        if not message.payload.get("ok", True):
            sim.set_case_status(case.status, reason_codes=["TICKET_FAILED"])
            return
        ticket = message.payload["ticket"]
        if ticket["id"] not in case.ticket_ids:
            case.ticket_ids.append(ticket["id"])
        sim.sync_case()

        if case.flow == "housekeeping":
            sim.set_case_status("DIGITAL_COMPLETED", event_details={"ticket": ticket["id"]})
            return
        if case.flow == "room_change":
            sim.enqueue(
                sim.make_message(
                    sender=self.agent_id,
                    receiver="reservation",
                    action=Action.FIND_ROOM_CANDIDATES.value,
                    payload={
                        "reservation_id": case.reservation_id,
                        "include_upgrade_alternatives": bool(
                            message.payload.get("include_upgrade_alternatives", False)
                        )
                        or sim.scenario.get("include_upgrade_alternatives", False),
                    },
                    correlation_id=f"TASK-ROOM-{case.case_id}",
                )
            )

    def _on_candidates_found(self, message: Message, sim: Any) -> None:
        case = sim.case
        if not message.payload.get("ok", True):
            sim.set_case_status("WAITING_HUMAN", reason_codes=["CANDIDATE_LOOKUP_FAILED"])
            return
        candidates = message.payload["candidates"]
        case.candidate_rooms = candidates
        sim.sync_case()

        if not candidates:
            sim.set_case_status("WAITING_HUMAN", reason_codes=["NO_CANDIDATE_ROOM"])
            return

        sim.create_investigator(
            candidates=candidates,
            constraints=dict(sim.scenario.get("constraints", {})),
            reservation_id=case.reservation_id,
            original_room_id=case.original_room_id,
        )
        sim.enqueue(
            sim.make_message(
                sender=self.agent_id,
                receiver="MA-001",
                action=Action.INSPECT_CANDIDATES.value,
                payload={"candidates": candidates, "constraints": dict(sim.scenario.get("constraints", {}))},
                correlation_id=f"TASK-INSPECT-{case.case_id}",
            )
        )

    def _on_inspection_result(self, message: Message, sim: Any) -> None:
        case = sim.case
        results = message.payload.get("results", [])
        case.inspection_results = results
        sim.sync_case()

        feasible = [item for item in results if item.get("is_routine_eligible")]
        case.evidence["inspection"] = results
        case.evidence["feasible_rooms"] = [item["room_id"] for item in feasible]
        case.evidence["alternatives"] = [
            item for item in results if not item.get("is_routine_eligible")
        ]
        sim.sync_case()

        if case.human_required:
            codes = list(case.human_reason_codes)
            for item in results:
                for code in item.get("reason_codes", []):
                    if code in ("UPGRADE_REQUIRES_HUMAN", "RATE_REQUIRES_HUMAN") and code not in codes:
                        codes.append(code)
            sim.set_case_status("WAITING_HUMAN", reason_codes=codes)
            return

        if not feasible:
            sim.set_case_status("WAITING_HUMAN", reason_codes=["NO_FEASIBLE_ROOM"])
            return

        chosen = sorted(feasible, key=lambda item: item["room_id"])[0]
        sim.propose_room_change(chosen["room_id"], chosen)

    def _on_folio_result(self, message: Message, sim: Any) -> None:
        case = sim.case
        if not message.payload.get("ok", True):
            sim.set_case_status("WAITING_HUMAN", reason_codes=["FOLIO_LOOKUP_FAILED"])
            return
        case.evidence["folio"] = {
            "entries": message.payload.get("entries", []),
            "total": message.payload.get("total", 0),
        }
        sim.sync_case()
        if case.flow == "billing_dispute":
            sim.set_case_status("WAITING_HUMAN", reason_codes=list(case.human_reason_codes))
        else:
            sim.set_case_status("DIGITAL_COMPLETED", event_details={"total": message.payload.get("total")})

    def _on_faq_result(self, message: Message, sim: Any) -> None:
        case = sim.case
        if not message.payload.get("ok", True):
            sim.set_case_status("WAITING_HUMAN", reason_codes=["FAQ_UNKNOWN"])
            return
        case.evidence["faq"] = {
            "key": message.payload.get("key"),
            "answer": message.payload.get("answer"),
        }
        sim.sync_case()
        sim.set_case_status("DIGITAL_COMPLETED", event_details={"answer": message.payload.get("answer")})

    def _on_guest_consent(self, message: Message, sim: Any) -> None:
        case = sim.case
        consent = message.payload
        if not consent.get("accepted"):
            sim.set_case_status("CLOSED_GUEST_DECLINED", reason_codes=["GUEST_DECLINED"])
            return
        case.consent = dict(consent)
        sim.set_case_status("PROCESSING", event_details={"consent": consent})
        case.recheck_correlation_id = f"RECHECK-{case.case_id}"
        sim.sync_case()
        sim.enqueue(
            sim.make_message(
                sender=self.agent_id,
                receiver="operations",
                action=Action.GET_READINESS.value,
                payload={"room_ids": [case.proposed_room_id]},
                correlation_id=case.recheck_correlation_id,
            )
        )

    def _on_readiness_result(self, message: Message, sim: Any) -> None:
        case = sim.case
        if message.correlation_id != case.recheck_correlation_id:
            sim.emit(
                EventType.TOOL_REFUSED.value,
                agent_id=self.agent_id,
                node_id=self.node_id,
                reason_codes=["CORRELATION_MISMATCH"],
                details={"correlation_id": message.correlation_id},
            )
            return
        if not message.payload.get("ok", True):
            sim.set_case_status("WAITING_HUMAN", reason_codes=["READINESS_LOOKUP_FAILED"])
            return
        case.recheck_readiness = message.payload.get("readiness", [])
        sim.sync_case()

        room_id = case.proposed_room_id
        fresh_readiness = next(
            (
                item
                for item in (case.recheck_readiness or [])
                if item.get("room_id") == room_id
            ),
            {},
        )
        sim.enqueue(
            sim.make_message(
                sender=self.agent_id,
                receiver="reservation",
                action=Action.COMMIT_ROOM_CHANGE.value,
                payload={
                    "reservation_id": case.reservation_id,
                    "target_room_id": room_id,
                    "case_id": case.case_id,
                    "expected_versions": {
                        "reservation": case.evidence.get("reservation_version"),
                        "original_room": case.evidence.get("original_room_version"),
                        "room": case.evidence.get("target_room_version"),
                        "readiness": case.evidence.get("proposal_evidence_version"),
                    },
                    "fresh_readiness": fresh_readiness,
                    "consent": case.consent,
                    "operation_key": f"roomchange:{case.case_id}:{room_id}",
                    "policy_decision": {
                        "human_required": case.human_required,
                        "decision_source": case.decision_source,
                        "reason_codes": case.human_reason_codes,
                    },
                    "case": case.to_dict(),
                    "recheck_correlation_id": message.correlation_id,
                    "expected_recheck_correlation": case.recheck_correlation_id,
                },
                correlation_id=f"TASK-COMMIT-{case.case_id}",
            )
        )

    def _on_room_change_result(self, message: Message, sim: Any) -> None:
        case = sim.case
        result = message.payload
        if result.get("ok"):
            case.assigned_room_id = result["result"]["to_room_id"]
            sim.sync_case()
            sim.set_case_status(
                "DIGITAL_COMPLETED",
                event_details={
                    "from_room_id": result["result"]["from_room_id"],
                    "to_room_id": result["result"]["to_room_id"],
                },
            )
        else:
            code = result.get("error", {}).get("code", "COMMIT_REFUSED")
            case.technical_failure = result.get("error")
            sim.sync_case()
            sim.set_case_status("WAITING_HUMAN", reason_codes=[code])


class MobileInvestigator(BaseAgent):
    """Agen beridentitas tetap yang instance aktifnya berpindah node."""

    capability_key = "investigator"
    code_version = "investigator-v1"
    schema_version = 1

    def __init__(
        self,
        agent_id: str = "MA-001",
        node_id: str = NodeId.FRONT_OFFICE.value,
        case_id: str = "CASE-001",
        goal: str = "FIND_READY_REPLACEMENT_ROOM",
        reservation_id: str = "RES001",
        original_room_id: str = "R101",
        constraints: Optional[Dict[str, Any]] = None,
        candidate_rooms: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(agent_id, node_id, case_id)
        self.goal = goal
        self.phase = AgentPhase.CREATED.value
        self.reservation_id = reservation_id
        self.original_room_id = original_room_id
        self.constraints = dict(constraints or {})
        self.candidate_rooms = list(candidate_rooms or [])
        self.visited_nodes = [node_id]
        self.inspection_results: List[Dict[str, Any]] = []
        self.migration_count = 0
        self.current_node = node_id

    @property
    def agent_type(self) -> str:
        return "mobile"

    def to_checkpoint(self) -> Dict[str, Any]:
        """Hanya field JSON-serializable; tanpa objek Python/koneksi/model."""
        return {
            "schema_version": self.schema_version,
            "code_version": self.code_version,
            "agent_id": self.agent_id,
            "case_id": self.case_id,
            "goal": self.goal,
            "phase": self.phase,
            "current_node": self.current_node,
            "reservation_id": self.reservation_id,
            "original_room_id": self.original_room_id,
            "constraints": dict(self.constraints),
            "candidate_rooms": [dict(item) for item in self.candidate_rooms],
            "visited_nodes": list(self.visited_nodes),
            "inspection_results": [dict(item) for item in self.inspection_results],
            "migration_count": self.migration_count,
        }

    @classmethod
    def from_checkpoint(cls, data: Dict[str, Any]) -> "MobileInvestigator":
        agent = cls(
            agent_id=data["agent_id"],
            node_id=data["current_node"],
            case_id=data["case_id"],
            goal=data["goal"],
            reservation_id=data.get("reservation_id", "RES001"),
            original_room_id=data.get("original_room_id", "R101"),
            constraints=data.get("constraints", {}),
            candidate_rooms=data.get("candidate_rooms", []),
        )
        agent.phase = data.get("phase", AgentPhase.INSPECT_LOCAL.value)
        agent.visited_nodes = list(data.get("visited_nodes", [data["current_node"]]))
        agent.inspection_results = list(data.get("inspection_results", []))
        agent.migration_count = int(data.get("migration_count", 0))
        agent.current_node = data["current_node"]
        return agent

    def state_snapshot(self) -> Dict[str, Any]:
        snapshot = super().state_snapshot()
        snapshot.update(
            {
                "goal": self.goal,
                "current_node": self.current_node,
                "phase": self.phase,
                "visited_nodes": list(self.visited_nodes),
                "migration_count": self.migration_count,
                "candidate_rooms": [dict(item) for item in self.candidate_rooms],
                "inspection_results": [dict(item) for item in self.inspection_results],
                "constraints": dict(self.constraints),
            }
        )
        return snapshot

    # ------------------------------------------------------------------ handle
    def handle(self, message: Message, sim: Any) -> None:
        self.last_action = message.action
        if message.action == Action.INSPECT_CANDIDATES.value:
            self._on_inspect(message, sim)
        elif message.action == Action.INSPECTION_RESULT.value:
            self._on_static_result(message, sim)
        else:
            sim.structured_failure(message, "UNKNOWN_ACTION", "Aksi tidak dikenal Investigator.")

    def _on_inspect(self, message: Message, sim: Any) -> None:
        if self.phase in (AgentPhase.CREATED.value, AgentPhase.READY_TO_MOVE.value):
            if message.payload.get("candidates"):
                self.candidate_rooms = list(message.payload["candidates"])
            if message.payload.get("constraints"):
                self.constraints = dict(message.payload["constraints"])
            if sim.mode == "mobile":
                self._start_mobile(sim)
            else:
                self._start_static(sim)
            return

        if self.phase == AgentPhase.INSPECT_LOCAL.value and self.node_id == NodeId.OPERATIONS.value:
            self._run_local_kernel(sim)
            return

        sim.emit(
            EventType.HANDLER_ERROR.value,
            agent_id=self.agent_id,
            node_id=self.node_id,
            details={"reason": "INSPECT_WRONG_PHASE", "phase": self.phase},
        )

    def _start_mobile(self, sim: Any) -> None:
        # Tetapkan phase kelanjutan SEBELUM serialisasi.
        self.phase = AgentPhase.INSPECT_LOCAL.value
        self.status = AgentRuntimeStatus.SUSPENDED.value
        self.last_action = "MIGRATE_TO_OPERATIONS"
        sim.begin_migration(self.agent_id, NodeId.OPERATIONS.value)

    def _start_static(self, sim: Any) -> None:
        self.phase = AgentPhase.INSPECT_LOCAL.value
        self.last_action = "DELEGATE_BATCH_INSPECTION"
        sim.enqueue(
            sim.make_message(
                sender=self.agent_id,
                receiver="operations",
                action=Action.INSPECT_CANDIDATES.value,
                payload={
                    "candidates": [dict(item) for item in self.candidate_rooms],
                    "constraints": dict(self.constraints),
                    "mode": "static_batch",
                },
                correlation_id=f"TASK-INSPECT-{self.case_id}",
            )
        )

    def _on_static_result(self, message: Message, sim: Any) -> None:
        if not message.payload.get("ok", True):
            self.phase = AgentPhase.FAILED.value
            self.status = AgentRuntimeStatus.FAILED.value
            sim.emit(
                EventType.TOOL_REFUSED.value,
                agent_id=self.agent_id,
                node_id=self.node_id,
                reason_codes=[message.payload.get("error", {}).get("code", "INSPECTION_FAILED")],
                details={"payload": message.payload},
            )
            sim.set_case_status("WAITING_HUMAN", reason_codes=["INSPECTION_FAILED"])
            return
        self.inspection_results = list(message.payload.get("results", []))
        self.phase = AgentPhase.DONE.value
        self.status = AgentRuntimeStatus.DONE.value
        self.last_action = "REPORT_INSPECTION_RESULT"
        sim.enqueue(
            sim.make_message(
                sender=self.agent_id,
                receiver="orchestrator",
                action=Action.INSPECTION_RESULT.value,
                payload={"results": self.inspection_results, "mode": "static_batch"},
                correlation_id=f"TASK-INSPECT-{self.case_id}",
            )
        )
        sim.archive_agent(self.agent_id)

    def _run_local_kernel(self, sim: Any) -> None:
        room_ids = [item["room_id"] for item in self.candidate_rooms]
        readiness = sim.read_local_readiness(self.agent_id, room_ids)
        if not readiness["ok"]:
            sim.emit(
                EventType.TOOL_REFUSED.value,
                agent_id=self.agent_id,
                node_id=self.node_id,
                reason_codes=[readiness["error"]["code"]],
                details={"error": readiness["error"]},
            )
            self.phase = AgentPhase.FAILED.value
            self.status = AgentRuntimeStatus.FAILED.value
            sim.set_case_status("WAITING_HUMAN", reason_codes=[readiness["error"]["code"]])
            return

        self.inspection_results = evaluate_candidates(
            self.candidate_rooms, readiness["readiness"], self.constraints
        )
        self.phase = AgentPhase.REPORT_RESULT.value
        sim.emit(
            EventType.LOCAL_INSPECTION_COMPLETED.value,
            agent_id=self.agent_id,
            node_id=self.node_id,
            details={
                "mode": "mobile_local",
                "room_ids": room_ids,
                "results": self.inspection_results,
            },
        )
        self.last_action = "REPORT_INSPECTION_RESULT"
        sim.enqueue(
            sim.make_message(
                sender=self.agent_id,
                receiver="orchestrator",
                action=Action.INSPECTION_RESULT.value,
                payload={"results": self.inspection_results, "mode": "mobile_local"},
                correlation_id=f"TASK-INSPECT-{self.case_id}",
            )
        )
        self.phase = AgentPhase.DONE.value
        self.status = AgentRuntimeStatus.DONE.value
        sim.archive_agent(self.agent_id)
