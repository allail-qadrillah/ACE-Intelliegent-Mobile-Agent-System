"""Engine simulator: node logis, message queue, event log, dan lifecycle kasus.

Satu proses Python, dua node logis, tanpa thread/background job.
"""

from __future__ import annotations

import json
import uuid
from collections import deque
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, List, Optional

from . import migration as migration_module
from . import policy
from .agents import (
    BaseAgent,
    BillingAgent,
    ConciergeAgent,
    DATA_CAPABILITIES,
    MobileInvestigator,
    OperationsAgent,
    OrchestratorAgent,
    ReservationAgent,
    ScenarioScoutAgent,
)
from .models import (
    Action,
    AgentPhase,
    AgentRuntimeStatus,
    Case,
    CaseStatus,
    Event,
    EventType,
    Message,
    MessageKind,
    MigrationStage,
    NodeId,
    PAUSED_STATUSES,
    TERMINAL_STATUSES,
    sha256_hex,
)
from .repository import (
    FrontOfficeRepository,
    OperationsRepository,
    err,
    load_seed,
    ok,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SCENARIOS_PATH = DATA_DIR / "scenarios.json"

SCENARIO_ORDER = ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09"]


def load_scenarios(path: Optional[Path] = None) -> Dict[str, Any]:
    target = Path(path) if path else SCENARIOS_PATH
    with open(target, "r", encoding="utf-8") as handle:
        return json.load(handle)


class GuestActorAgent(BaseAgent):
    capability_key = "guest"

    def __init__(self, node_id: str = NodeId.FRONT_OFFICE.value) -> None:
        super().__init__("guest", node_id)

    def handle(self, message: Message, sim: Any) -> None:  # pragma: no cover
        sim.emit(
            EventType.HANDLER_ERROR.value,
            agent_id=self.agent_id,
            node_id=self.node_id,
            details={"reason": "GUEST_IS_ROLEPLAY_ACTOR"},
        )


class StaffActorAgent(BaseAgent):
    capability_key = "staff"

    def __init__(self, node_id: str = NodeId.FRONT_OFFICE.value) -> None:
        super().__init__("staff", node_id)

    def handle(self, message: Message, sim: Any) -> None:  # pragma: no cover
        sim.emit(
            EventType.STAFF_ACTION.value,
            agent_id=self.agent_id,
            node_id=self.node_id,
            details={"reason": "STAFF_ACTION_VIA_UI"},
        )


class NodeRuntime:
    def __init__(self, node_id: str, repository: Any) -> None:
        self.node_id = node_id
        self.repository = repository
        self.active_agents: Dict[str, BaseAgent] = {}
        self.active = True

    def register(self, agent: BaseAgent) -> None:
        agent.node_id = self.node_id
        self.active_agents[agent.agent_id] = agent

    def unregister(self, agent_id: str) -> Optional[BaseAgent]:
        return self.active_agents.pop(agent_id, None)


class Simulation:
    def __init__(
        self,
        *,
        mode: str = "mobile",
        scenario_id: str = "S01",
        model: Any,
        seed_path: Optional[Path] = None,
        scenarios_path: Optional[Path] = None,
        run_id: Optional[str] = None,
        threshold: float = policy.DEFAULT_THRESHOLD,
        enable_audit: bool = True,
    ) -> None:
        if mode not in ("mobile", "static"):
            raise ValueError("mode harus 'mobile' atau 'static'.")
        scenarios = load_scenarios(scenarios_path)
        if scenario_id not in scenarios:
            raise ValueError(f"Scenario {scenario_id} tidak dikenal.")
        self.scenarios = scenarios
        self.scenario_id = scenario_id
        self.scenario = scenarios[scenario_id]
        self.mode = mode
        self.active_mode = mode
        self.run_id = run_id or f"run-{uuid.uuid4().hex[:8]}"
        self.model = model
        self.threshold = float(threshold)
        self.enable_audit = enable_audit

        seed = load_seed(seed_path)
        overrides = self.scenario.get("seed_overrides", {})
        self.front_office = FrontOfficeRepository(seed, overrides)
        self.operations = OperationsRepository(seed, overrides)

        self.nodes: Dict[str, NodeRuntime] = {
            NodeId.FRONT_OFFICE.value: NodeRuntime(NodeId.FRONT_OFFICE.value, self.front_office),
            NodeId.OPERATIONS.value: NodeRuntime(NodeId.OPERATIONS.value, self.operations),
        }

        self.agents: Dict[str, BaseAgent] = {}
        self.owner_by_agent: Dict[str, Optional[str]] = {}
        self.archived: Dict[str, Dict[str, Any]] = {}
        self.messages: List[Dict[str, Any]] = []
        self.events: List[Event] = []
        self.queue: deque = deque()
        self.processed_message_ids: set = set()
        self.case: Optional[Case] = None
        self.migration = None
        self.last_migration = None
        self.migration_counter = 1
        self.message_counter = 0
        self.step_index = 0
        self.metrics: Dict[str, Any] = {
            "messages_sent": 0,
            "inter_node_messages": 0,
            "inter_node_message_bytes": 0,
            "transferred_checkpoint_bytes": 0,
            "migrations_succeeded": 0,
            "migrations_failed": 0,
            "engine_steps": 0,
            "tool_calls": 0,
            "policy_refusals": 0,
            "duplicate_side_effects": 0,
            "duplicates_ignored": 0,
            "engine_compute_ms": 0.0,
        }

        self._register_static_agents()

    # ------------------------------------------------------------- registrasi
    def _register_static_agents(self) -> None:
        front_office = self.nodes[NodeId.FRONT_OFFICE.value]
        operations = self.nodes[NodeId.OPERATIONS.value]
        static_agents = [
            ScenarioScoutAgent(),
            OrchestratorAgent(),
            ReservationAgent(),
            BillingAgent(),
            ConciergeAgent(),
            GuestActorAgent(),
            StaffActorAgent(),
        ]
        for agent in static_agents:
            self.agents[agent.agent_id] = agent
            front_office.register(agent)
            self.owner_by_agent[agent.agent_id] = NodeId.FRONT_OFFICE.value
        ops_agent = OperationsAgent()
        self.agents[ops_agent.agent_id] = ops_agent
        operations.register(ops_agent)
        self.owner_by_agent[ops_agent.agent_id] = NodeId.OPERATIONS.value

    # ------------------------------------------------------------------ util
    def node_repo(self, node_id: str) -> Any:
        return self.nodes[node_id].repository

    def node_is_active(self, node_id: str) -> bool:
        node = self.nodes.get(node_id)
        return bool(node and node.active)

    def node_supports_data(self, node_id: str, capability: str) -> bool:
        return capability in DATA_CAPABILITIES.get(node_id, set())

    def active_instance_count(self, agent_id: str) -> int:
        return sum(
            1 for node in self.nodes.values() if agent_id in node.active_agents
        )

    def agent_node(self, agent_id: str) -> Optional[str]:
        agent = self.agents.get(agent_id)
        if agent is not None:
            return agent.node_id
        owner = self.owner_by_agent.get(agent_id)
        if owner:
            return owner
        if self.migration and self.migration.agent_id == agent_id:
            return self.migration.destination_node
        return None

    def emit(
        self,
        event_type: str,
        *,
        agent_id: Optional[str] = None,
        node_id: Optional[str] = None,
        source_node: Optional[str] = None,
        destination_node: Optional[str] = None,
        message_id: Optional[str] = None,
        migration_id: Optional[str] = None,
        reason_codes: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
        case_id: Optional[str] = None,
    ) -> Event:
        resolved_case_id = case_id
        if resolved_case_id is None and self.case is not None:
            resolved_case_id = self.case.case_id
        event = Event(
            seq=len(self.events) + 1,
            run_id=self.run_id,
            case_id=resolved_case_id,
            step_index=self.step_index,
            event_type=event_type,
            agent_id=agent_id,
            node_id=node_id,
            source_node=source_node,
            destination_node=destination_node,
            message_id=message_id,
            migration_id=migration_id,
            reason_codes=list(reason_codes or []),
            details=dict(details or {}),
        )
        self.events.append(event)
        if event_type == EventType.TOOL_SUCCEEDED.value:
            self.metrics["tool_calls"] += 1
        elif event_type == EventType.TOOL_REFUSED.value:
            self.metrics["policy_refusals"] += 1
        if self.enable_audit:
            self.front_office.append_audit(event_type, event.to_dict())
        return event

    def structured_failure(self, message: Message, code: str, text: str) -> None:
        self.emit(
            EventType.HANDLER_ERROR.value,
            agent_id=message.receiver,
            node_id=self.agent_node(message.receiver),
            message_id=message.message_id,
            reason_codes=[code],
            details={"code": code, "message": text, "action": message.action},
            case_id=message.case_id,
        )

    def tool_refused(self, agent: BaseAgent, message: Message, error: Dict[str, Any]) -> None:
        self.emit(
            EventType.TOOL_REFUSED.value,
            agent_id=agent.agent_id,
            node_id=agent.node_id,
            message_id=message.message_id,
            reason_codes=[error.get("code", "TOOL_REFUSED")],
            details={"error": error, "action": message.action},
        )

    def make_message(
        self,
        *,
        sender: str,
        receiver: str,
        action: str,
        payload: Optional[Dict[str, Any]] = None,
        kind: str = MessageKind.REQUEST.value,
        correlation_id: Optional[str] = None,
        source_node: Optional[str] = None,
        destination_node: Optional[str] = None,
    ) -> Message:
        self.message_counter += 1
        case_id = self.case.case_id if self.case else "CASE-001"
        return Message(
            message_id=f"MSG-{self.message_counter:03d}",
            run_id=self.run_id,
            case_id=case_id,
            sender=sender,
            receiver=receiver,
            source_node=source_node if source_node is not None else self.agent_node(sender),
            destination_node=destination_node
            if destination_node is not None
            else self.agent_node(receiver),
            kind=kind,
            action=action,
            correlation_id=correlation_id,
            payload=dict(payload or {}),
        )

    def enqueue(self, message: Message) -> None:
        self.queue.append(message)
        self.messages.append(message.to_dict())
        self.metrics["messages_sent"] += 1
        if message.source_node != message.destination_node:
            self.metrics["inter_node_messages"] += 1
            self.metrics["inter_node_message_bytes"] += len(message.canonical_bytes())
        self.emit(
            EventType.MESSAGE_SENT.value,
            agent_id=message.sender,
            node_id=message.source_node,
            source_node=message.source_node,
            destination_node=message.destination_node,
            message_id=message.message_id,
            details={
                "action": message.action,
                "receiver": message.receiver,
                "correlation_id": message.correlation_id,
                "kind": message.kind,
            },
            case_id=message.case_id,
        )

    # ------------------------------------------------------------ case state
    def sync_case(self) -> None:
        if self.case is not None:
            self.front_office.sync_case(self.case.to_dict())

    def create_case(self, payload: Dict[str, Any]) -> Case:
        reservation = self.front_office.get_reservation("RES001")
        original_room = reservation["reservation"]["room_id"] if reservation["ok"] else "R101"
        case = Case(
            case_id="CASE-001",
            run_id=self.run_id,
            scenario_id=payload["scenario_id"],
            intent=payload["intent"],
            flow=payload["flow"],
            guest_message=payload["guest_message"],
            features=payload["features"],
            status=CaseStatus.PROCESSING.value,
            reservation_id="RES001",
            original_room_id=original_room,
        )
        self.case = case
        self.sync_case()
        self.emit(
            EventType.CASE_CREATED.value,
            agent_id="orchestrator",
            node_id=NodeId.FRONT_OFFICE.value,
            details={
                "scenario_id": case.scenario_id,
                "flow": case.flow,
                "intent": case.intent,
                "status": case.status,
            },
        )
        return case

    def apply_policy_decision(self, decision: policy.PolicyDecision) -> None:
        case = self.case
        case.human_required = bool(case.human_required or decision.human_required)
        for code in decision.reason_codes:
            if code not in case.human_reason_codes:
                case.human_reason_codes.append(code)
        for code in decision.mandatory_reasons:
            if code not in case.mandatory_reasons:
                case.mandatory_reasons.append(code)
        case.decision_source = decision.decision_source
        case.p_human = decision.p_human
        case.model_recommends_human = decision.model_recommends_human
        if decision.priority == "URGENT":
            case.priority = "URGENT"
        case.decision_history.append(decision.to_dict())
        self.sync_case()

    def set_case_status(
        self,
        status: str,
        *,
        reason_codes: Optional[List[str]] = None,
        event_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        case = self.case
        if case is None:
            return
        previous = case.status
        case.status = status
        if reason_codes:
            for code in reason_codes:
                if code and code not in case.human_reason_codes:
                    case.human_reason_codes.append(code)
        if status == CaseStatus.WAITING_HUMAN.value:
            case.human_required = True
            if case.decision_source == "POLICY_AND_ML":
                case.decision_source = "POLICY"
        self.sync_case()
        details = {"from": previous, "to": status}
        if reason_codes:
            details["reason_codes"] = list(reason_codes)
        if event_details:
            details.update(event_details)
        self.emit(
            EventType.CASE_STATUS_CHANGED.value,
            agent_id="orchestrator",
            node_id=NodeId.FRONT_OFFICE.value,
            reason_codes=list(reason_codes or []),
            details=details,
        )

    def propose_room_change(self, room_id: str, inspection_item: Dict[str, Any]) -> None:
        case = self.case
        reservation = self.front_office.get_reservation(case.reservation_id)["reservation"]
        original_room = self.front_office.get_room(case.original_room_id)["room"]
        case.proposed_room_id = room_id
        case.proposal_version += 1
        case.evidence["reservation_version"] = reservation["version"]
        case.evidence["original_room_version"] = original_room["version"]
        case.evidence["target_room_version"] = inspection_item.get("room_version")
        case.evidence["proposal_evidence_version"] = inspection_item.get("evidence_version")
        self.sync_case()
        self.emit(
            EventType.CANDIDATES_PROPOSED.value,
            agent_id="orchestrator",
            node_id=NodeId.FRONT_OFFICE.value,
            details={
                "proposed_room_id": room_id,
                "proposal_version": case.proposal_version,
                "inspection": inspection_item,
            },
        )
        self.set_case_status(CaseStatus.WAITING_GUEST.value)

    # ------------------------------------------------------------- investigator
    def create_investigator(
        self,
        *,
        candidates: List[Dict[str, Any]],
        constraints: Dict[str, Any],
        reservation_id: str,
        original_room_id: str,
    ) -> MobileInvestigator:
        reservation = self.front_office.get_reservation(reservation_id)
        rate = reservation["reservation"]["nightly_rate"] if reservation["ok"] else 500000
        resolved_constraints = dict(constraints)
        resolved_constraints.setdefault("reservation_rate", rate)
        agent = MobileInvestigator(
            agent_id="MA-001",
            node_id=NodeId.FRONT_OFFICE.value,
            case_id=self.case.case_id if self.case else "CASE-001",
            goal="FIND_READY_REPLACEMENT_ROOM",
            reservation_id=reservation_id,
            original_room_id=original_room_id,
            constraints=resolved_constraints,
            candidate_rooms=candidates,
        )
        agent.phase = AgentPhase.READY_TO_MOVE.value
        self.agents[agent.agent_id] = agent
        self.nodes[NodeId.FRONT_OFFICE.value].register(agent)
        self.owner_by_agent[agent.agent_id] = NodeId.FRONT_OFFICE.value
        self.emit(
            EventType.AGENT_CREATED.value,
            agent_id=agent.agent_id,
            node_id=agent.node_id,
            details={"agent_type": "mobile", "goal": agent.goal, "candidates": candidates},
        )
        return agent

    def archive_agent(self, agent_id: str) -> None:
        for node in self.nodes.values():
            node.active_agents.pop(agent_id, None)
        agent = self.agents.get(agent_id)
        if agent is not None:
            self.archived[agent_id] = agent.state_snapshot()
        self.owner_by_agent[agent_id] = None

    def begin_migration(self, agent_id: str, destination_node: str):
        return migration_module.begin(self, agent_id, destination_node)

    # ------------------------------------------------------------- local read
    def read_local_readiness(self, agent_id: str, room_ids: List[str]) -> Dict[str, Any]:
        """Guarded local read: registry/owner/capability diperiksa runtime."""
        agent = self.agents.get(agent_id)
        if agent is None:
            return err("UNKNOWN_AGENT", "Agen tidak terdaftar.", {"agent_id": agent_id})
        if agent.node_id != NodeId.OPERATIONS.value:
            return err(
                "WRONG_NODE",
                "Akses readiness lokal hanya tersedia di node OPERATIONS.",
                {"agent_node": agent.node_id},
            )
        if self.owner_by_agent.get(agent_id) != NodeId.OPERATIONS.value:
            return err(
                "NOT_OWNER",
                "Agen tidak dimiliki node OPERATIONS saat ini.",
                {"owner": self.owner_by_agent.get(agent_id)},
            )
        if agent_id not in self.nodes[NodeId.OPERATIONS.value].active_agents:
            return err(
                "NOT_ACTIVE", "Agen tidak aktif pada registry node OPERATIONS.", {"agent_id": agent_id}
            )
        if "inspect_readiness" not in agent.capabilities:
            return err(
                "MISSING_CAPABILITY",
                "Agen tidak memiliki capability inspect_readiness.",
                {"capabilities": list(agent.capabilities)},
            )
        return self.operations.get_readiness(room_ids)

    # ----------------------------------------------------------------- engine
    def start_scenario(self) -> None:
        scout = self.agents["scenario_scout"]
        message = scout.build_start_message(self.scenario, self.run_id)
        self.case = None
        self.enqueue(message)

    def has_pending_work(self) -> bool:
        if self.queue:
            return True
        return bool(
            self.migration is not None
            and self.migration.stage
            in (
                MigrationStage.INITIATED.value,
                MigrationStage.PREPARED.value,
                MigrationStage.DEPARTED.value,
            )
        )

    def is_paused(self) -> bool:
        if self.has_pending_work():
            return False
        if self.case is None:
            return True
        return self.case.status in {status.value for status in PAUSED_STATUSES}

    def step(self) -> Dict[str, Any]:
        start = perf_counter()
        self.step_index += 1
        self.metrics["engine_steps"] += 1
        try:
            if self.migration is not None and self.migration.stage in (
                MigrationStage.INITIATED.value,
                MigrationStage.PREPARED.value,
                MigrationStage.DEPARTED.value,
            ):
                self._advance_migration()
            elif self.queue:
                message = self.queue.popleft()
                self._deliver(message)
        finally:
            self.metrics["engine_compute_ms"] += (perf_counter() - start) * 1000.0
        return self.snapshot()

    def _deliver(self, message: Message) -> None:
        self.emit(
            EventType.MESSAGE_DELIVERED.value,
            agent_id=message.receiver,
            node_id=message.destination_node,
            source_node=message.source_node,
            destination_node=message.destination_node,
            message_id=message.message_id,
            details={"action": message.action},
            case_id=message.case_id,
        )
        if message.message_id in self.processed_message_ids:
            self.metrics["duplicates_ignored"] += 1
            self.emit(
                EventType.DUPLICATE_IGNORED.value,
                message_id=message.message_id,
                details={"action": message.action, "receiver": message.receiver},
                case_id=message.case_id,
            )
            return
        self.processed_message_ids.add(message.message_id)

        agent = self.agents.get(message.receiver)
        if agent is None:
            self.structured_failure(message, "UNKNOWN_RECEIVER", "Penerima pesan tidak terdaftar.")
            return
        if message.action not in {action.value for action in Action}:
            self.structured_failure(message, "UNKNOWN_ACTION", "Aksi pesan tidak dikenal.")
            return
        try:
            agent.handle(message, self)
        except Exception as exc:  # pragma: no cover - jalur pertahanan
            self.structured_failure(message, "HANDLER_EXCEPTION", repr(exc))
            if self.case is not None and self.case.status not in {
                status.value for status in TERMINAL_STATUSES
            }:
                self.set_case_status(
                    CaseStatus.WAITING_HUMAN.value, reason_codes=["HANDLER_EXCEPTION"]
                )

    def _advance_migration(self) -> None:
        record = self.migration
        stage_at_start = record.stage
        try:
            if record.stage == MigrationStage.INITIATED.value:
                migration_module.prepare(self, record)
            elif record.stage == MigrationStage.PREPARED.value:
                migration_module.depart(self, record)
            elif record.stage == MigrationStage.DEPARTED.value:
                migration_module.arrive(self, record)
        except migration_module.MigrationError as exc:
            self._handle_migration_failure(record, exc, stage_at_start)

    def _handle_migration_failure(
        self, record: Any, exc: migration_module.MigrationError, stage_at_start: str
    ) -> None:
        record.stage = MigrationStage.FAILED.value
        record.error = exc.to_dict()
        self.metrics["migrations_failed"] += 1
        self.emit(
            EventType.MIGRATION_FAILED.value,
            agent_id=record.agent_id,
            node_id=record.source_node,
            migration_id=record.migration_id,
            source_node=record.source_node,
            destination_node=record.destination_node,
            reason_codes=[exc.code],
            details=exc.to_dict(),
        )

        departed = stage_at_start == MigrationStage.DEPARTED.value
        restored = False
        if departed:
            restored = migration_module.restore_source(self, record)
        else:
            agent = self.agents.get(record.agent_id)
            if agent is not None:
                agent.status = AgentRuntimeStatus.ACTIVE.value
                agent.phase = AgentPhase.READY_TO_MOVE.value
                self.nodes[record.source_node].register(agent)
                self.owner_by_agent[record.agent_id] = record.source_node
                restored = True

        agent = self.agents.get(record.agent_id)
        if agent is not None and departed:
            # Sesudah DEPART, migrasi yang gagal menandai investigator FAILED.
            agent.status = AgentRuntimeStatus.FAILED.value
            agent.phase = AgentPhase.FAILED.value
        if agent is not None:
            agent.last_action = f"MIGRATION_FAILED:{exc.code}"

        self.migration = None
        self.last_migration = record

        if self.case is not None:
            self.case.technical_failure = exc.to_dict()
            if restored:
                self.set_case_status(
                    CaseStatus.WAITING_HUMAN.value,
                    reason_codes=["MIGRATION_FAILED", exc.code],
                )
            else:
                self.set_case_status(
                    CaseStatus.FAILED.value,
                    reason_codes=["MIGRATION_FAILED", exc.code, "RESTORE_IMPOSSIBLE"],
                )

    def run_until_pause(self, max_steps: int = 100) -> int:
        steps = 0
        while self.has_pending_work():
            if steps >= max_steps:
                raise RuntimeError(
                    f"run_until_pause melewati batas {max_steps} langkah; kemungkinan loop."
                )
            self.step()
            steps += 1
        return steps

    # ------------------------------------------------------------- aksi domain
    def submit_guest_choice(self, accept: bool, actor: str = "GUEST") -> Dict[str, Any]:
        start = perf_counter()
        try:
            case = self.case
            if (
                case is None
                or case.status != CaseStatus.WAITING_GUEST.value
                or not case.proposed_room_id
            ):
                return {"ok": False, "reason": "NOT_WAITING_GUEST", "snapshot": self.snapshot()}

            consent = {
                "case_id": case.case_id,
                "proposed_room_id": case.proposed_room_id,
                "proposal_version": case.proposal_version,
                "accepted": bool(accept),
                "actor": actor,
            }
            case.consent = consent
            self.emit(
                EventType.GUEST_CONSENT_RECORDED.value,
                agent_id="guest",
                node_id=NodeId.FRONT_OFFICE.value,
                details=consent,
            )
            if not accept:
                self.sync_case()
                self.set_case_status(
                    CaseStatus.CLOSED_GUEST_DECLINED.value, reason_codes=["GUEST_DECLINED"]
                )
                return {"ok": True, "accepted": False, "snapshot": self.snapshot()}

            self.sync_case()
            self.enqueue(
                self.make_message(
                    sender="guest",
                    receiver="orchestrator",
                    action=Action.GUEST_CONSENT.value,
                    payload=consent,
                    correlation_id=f"CONSENT-{case.case_id}",
                )
            )
            return {"ok": True, "accepted": True, "snapshot": self.snapshot()}
        finally:
            self.metrics["engine_compute_ms"] += (perf_counter() - start) * 1000.0

    def staff_take_over(self) -> Dict[str, Any]:
        case = self.case
        if case is None or case.status != CaseStatus.WAITING_HUMAN.value:
            return {"ok": False, "reason": "NOT_WAITING_HUMAN"}
        self.emit(
            EventType.STAFF_ACTION.value,
            agent_id="staff",
            node_id=NodeId.FRONT_OFFICE.value,
            details={"action": "TAKE_OVER"},
        )
        self.set_case_status(CaseStatus.HUMAN_HANDLING.value)
        return {"ok": True}

    def staff_close_case(self, note: str) -> Dict[str, Any]:
        case = self.case
        if case is None or case.status != CaseStatus.HUMAN_HANDLING.value:
            return {"ok": False, "reason": "NOT_HUMAN_HANDLING"}
        if not note or not note.strip():
            return {"ok": False, "reason": "NOTE_REQUIRED"}
        case.closed_note = note.strip()
        self.emit(
            EventType.STAFF_ACTION.value,
            agent_id="staff",
            node_id=NodeId.FRONT_OFFICE.value,
            details={"action": "CLOSE_CASE", "note": case.closed_note},
        )
        self.set_case_status(CaseStatus.CLOSED_BY_STAFF.value)
        return {"ok": True}

    def staff_update_ticket(self, ticket_id: str, next_status: str) -> Dict[str, Any]:
        result = self.operations.update_ticket_status(ticket_id, next_status, actor="STAFF")
        if result["ok"]:
            self.emit(
                EventType.TICKET_UPDATED.value,
                agent_id="staff",
                node_id=NodeId.OPERATIONS.value,
                details={"ticket": result["ticket"]},
            )
        else:
            self.emit(
                EventType.TOOL_REFUSED.value,
                agent_id="staff",
                node_id=NodeId.OPERATIONS.value,
                reason_codes=[result["error"]["code"]],
                details={"error": result["error"]},
            )
        return result

    def list_tickets(self) -> List[Dict[str, Any]]:
        return self.operations.list_tickets()

    # --------------------------------------------------------------- snapshot
    def agent_cards(self) -> List[Dict[str, Any]]:
        cards = []
        for node_id, node in self.nodes.items():
            for agent_id, agent in node.active_agents.items():
                card = agent.state_snapshot()
                card["location"] = node_id
                card["archived"] = False
                cards.append(card)
        for agent_id, snapshot in self.archived.items():
            card = dict(snapshot)
            card["location"] = snapshot.get("node_id")
            card["archived"] = True
            cards.append(card)
        return cards

    def snapshot(self) -> Dict[str, Any]:
        migration = self.migration or self.last_migration
        return {
            "run_id": self.run_id,
            "mode": self.mode,
            "active_mode": self.active_mode,
            "scenario_id": self.scenario_id,
            "scenario": self.scenario,
            "threshold": self.threshold,
            "step_index": self.step_index,
            "case": None if self.case is None else self.case.to_dict(),
            "nodes": {
                node_id: {
                    "active": node.active,
                    "active_agents": list(node.active_agents.keys()),
                }
                for node_id, node in self.nodes.items()
            },
            "agents": self.agent_cards(),
            "owner_by_agent": dict(self.owner_by_agent),
            "migration": None if migration is None else migration.to_dict(),
            "migration_stage": None if migration is None else migration.stage,
            "queue": [message.to_dict() for message in self.queue],
            "has_pending_work": self.has_pending_work(),
            "is_paused": self.is_paused(),
            "metrics": dict(self.metrics),
            "tickets": self.list_tickets(),
        }

    def metrics(self) -> Dict[str, Any]:  # pragma: no cover - alias kenyamanan
        return dict(self.metrics)

    def export(self) -> Dict[str, Any]:
        return {
            "metadata": {
                "app": "Demo Mobile Agent Hotel",
                "version": "1.0.0",
                "run_id": self.run_id,
                "scenario_id": self.scenario_id,
                "mode": self.mode,
                "threshold": self.threshold,
                "model": getattr(self.model, "report", None),
            },
            "initial_seed_scenario": self.scenario,
            "case": None if self.case is None else self.case.to_dict(),
            "events": [event.to_dict() for event in self.events],
            "messages": list(self.messages),
            "checkpoints": {
                "last_migration": None
                if self.last_migration is None
                else self.last_migration.to_dict(),
            },
            "databases": {
                "front_office": self.front_office.dump(),
                "operations": self.operations.dump(),
            },
            "metrics": {
                **self.metrics,
                "total_simulated_payload_bytes": self.metrics["inter_node_message_bytes"]
                + self.metrics["transferred_checkpoint_bytes"],
            },
            "snapshot": self.snapshot(),
        }

    def export_json(self) -> str:
        return json.dumps(self.export(), indent=2, ensure_ascii=False, sort_keys=True)

    def checkpoint_hash(self) -> Optional[str]:
        record = self.migration or self.last_migration
        if record is None or record.original_bytes is None:
            return None
        return sha256_hex(record.original_bytes)

    def close(self) -> None:
        self.front_office.close()
        self.operations.close()
