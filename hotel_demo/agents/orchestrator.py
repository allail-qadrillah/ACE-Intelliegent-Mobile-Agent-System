"""Orchestrator Agent (node Front Office): pengatur alur satu kasus tamu.

Orchestrator tidak mengakses data sendiri; ia menerima pesan hasil dari agen
lain lalu memutuskan langkah berikutnya. Alur per ``flow``:

- ``room_change``   : tiket maintenance → cari kandidat → investigator inspeksi
                      → usulkan kamar → consent tamu → recheck readiness → commit
- ``housekeeping``  : tiket housekeeping → selesai
- ``billing_*``     : ambil folio → selesai / serahkan ke staf (dispute)
- ``faq``           : ambil jawaban FAQ → selesai
"""

from __future__ import annotations

from typing import Any

from .. import policy
from ..models import Action, EventType, Message, NodeId
from .base import BaseAgent


class OrchestratorAgent(BaseAgent):
    capability_key = "orchestrator"

    def __init__(self, node_id: str = NodeId.FRONT_OFFICE.value) -> None:
        super().__init__("orchestrator", node_id)

    def handle(self, message: Message, sim: Any) -> None:
        """Arahkan pesan ke handler sesuai ``message.action``."""
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
        """Langkah pertama: triase (model ML + policy), buat kasus, lalu delegasi."""
        payload = message.payload
        features = payload["features"]
        flags = payload.get("flags", {})

        # 1. Model ML memprediksi peluang kasus perlu ditangani manusia.
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
        # 2. Policy (rules) memutuskan final, bisa meng-override model.
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

        # 3. Delegasikan ke agen yang tepat sesuai jenis alur.
        flow = case.flow
        if flow in ("room_change", "housekeeping"):
            if flow == "room_change":
                department = "MAINTENANCE"
                description = f"Perbaikan AC kamar {case.original_room_id}"
                suffix = "maintenance"
            else:
                department = "HOUSEKEEPING"
                if "bantal" in case.guest_message.lower():
                    description = f"Antar bantal ke kamar {case.original_room_id}"
                else:
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

    # ------------------------------------------------------ alur tiket/kamar
    def _on_ticket_created(self, message: Message, sim: Any) -> None:
        """Tiket jadi: housekeeping selesai; room_change lanjut cari kamar pengganti."""
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
        """Ada kandidat kamar: buat MobileInvestigator dan minta ia menginspeksi."""
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
        """Hasil inspeksi masuk: pilih kamar layak, atau serahkan ke staf."""
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

        # Policy sudah menandai perlu manusia → kumpulkan alasan lalu tunggu staf.
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

        # Pilihan deterministik: room_id terkecil di antara kamar layak.
        chosen = sorted(feasible, key=lambda item: item["room_id"])[0]
        sim.propose_room_change(chosen["room_id"], chosen)

    # ---------------------------------------------------- alur billing & faq
    def _on_folio_result(self, message: Message, sim: Any) -> None:
        """Folio diterima: dispute → staf; sekadar lihat rincian → selesai."""
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
        """Jawaban FAQ diterima: simpan sebagai evidence lalu selesai."""
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

    # ------------------------------------------- consent → recheck → commit
    def _on_guest_consent(self, message: Message, sim: Any) -> None:
        """Tamu setuju pindah → recheck readiness kamar tujuan dulu (data bisa berubah)."""
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
        """Hasil recheck diterima → kirim perintah commit ke Reservation Agent."""
        case = sim.case
        # Abaikan balasan yang bukan milik recheck kasus ini.
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
        # expected_versions: versi data saat usulan dibuat. Repo menolak commit
        # jika data sudah berubah sejak itu (optimistic concurrency).
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
        """Commit berhasil → kasus selesai; gagal → serahkan ke staf dengan kode error."""
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
