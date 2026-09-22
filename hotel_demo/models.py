"""Model domain: enum, dataclass, dan kontrak pesan/event/migrasi.

Modul ini tidak bergantung pada Streamlit, SQLite, atau scikit-learn sehingga
dapat diuji secara terpisah.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class NodeId(str, Enum):
    FRONT_OFFICE = "FRONT_OFFICE"
    OPERATIONS = "OPERATIONS"


class CaseStatus(str, Enum):
    CREATED = "CREATED"
    PROCESSING = "PROCESSING"
    WAITING_GUEST = "WAITING_GUEST"
    WAITING_HUMAN = "WAITING_HUMAN"
    HUMAN_HANDLING = "HUMAN_HANDLING"
    DIGITAL_COMPLETED = "DIGITAL_COMPLETED"
    CLOSED_GUEST_DECLINED = "CLOSED_GUEST_DECLINED"
    CLOSED_BY_STAFF = "CLOSED_BY_STAFF"
    FAILED = "FAILED"


TERMINAL_STATUSES = {
    CaseStatus.DIGITAL_COMPLETED,
    CaseStatus.CLOSED_GUEST_DECLINED,
    CaseStatus.CLOSED_BY_STAFF,
    CaseStatus.FAILED,
}

PAUSED_STATUSES = TERMINAL_STATUSES | {
    CaseStatus.WAITING_GUEST,
    CaseStatus.WAITING_HUMAN,
    CaseStatus.HUMAN_HANDLING,
}


class AgentRuntimeStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    IN_TRANSIT = "IN_TRANSIT"
    DONE = "DONE"
    FAILED = "FAILED"


class AgentPhase(str, Enum):
    CREATED = "CREATED"
    READY_TO_MOVE = "READY_TO_MOVE"
    INSPECT_LOCAL = "INSPECT_LOCAL"
    REPORT_RESULT = "REPORT_RESULT"
    DONE = "DONE"
    FAILED = "FAILED"


class MessageKind(str, Enum):
    REQUEST = "REQUEST"
    INFORM = "INFORM"
    FAILURE = "FAILURE"


class Action(str, Enum):
    START_CASE = "START_CASE"
    TRIAGE_RESULT = "TRIAGE_RESULT"
    CREATE_TICKET = "CREATE_TICKET"
    TICKET_CREATED = "TICKET_CREATED"
    FIND_ROOM_CANDIDATES = "FIND_ROOM_CANDIDATES"
    CANDIDATES_FOUND = "CANDIDATES_FOUND"
    INSPECT_CANDIDATES = "INSPECT_CANDIDATES"
    INSPECTION_RESULT = "INSPECTION_RESULT"
    GET_READINESS = "GET_READINESS"
    READINESS_RESULT = "READINESS_RESULT"
    GET_FOLIO = "GET_FOLIO"
    FOLIO_RESULT = "FOLIO_RESULT"
    GET_FAQ = "GET_FAQ"
    FAQ_RESULT = "FAQ_RESULT"
    GUEST_CONSENT = "GUEST_CONSENT"
    COMMIT_ROOM_CHANGE = "COMMIT_ROOM_CHANGE"
    ROOM_CHANGE_RESULT = "ROOM_CHANGE_RESULT"
    STAFF_ACTION = "STAFF_ACTION"


class MigrationStage(str, Enum):
    INITIATED = "INITIATED"
    PREPARED = "PREPARED"
    DEPARTED = "DEPARTED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class TicketStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class EventType(str, Enum):
    CASE_CREATED = "CASE_CREATED"
    CASE_STATUS_CHANGED = "CASE_STATUS_CHANGED"
    MESSAGE_SENT = "MESSAGE_SENT"
    MESSAGE_DELIVERED = "MESSAGE_DELIVERED"
    MODEL_PREDICTED = "MODEL_PREDICTED"
    POLICY_EVALUATED = "POLICY_EVALUATED"
    TOOL_SUCCEEDED = "TOOL_SUCCEEDED"
    TOOL_REFUSED = "TOOL_REFUSED"
    MIGRATION_PREPARED = "MIGRATION_PREPARED"
    MIGRATION_DEPARTED = "MIGRATION_DEPARTED"
    MIGRATION_ARRIVED = "MIGRATION_ARRIVED"
    MIGRATION_FAILED = "MIGRATION_FAILED"
    LOCAL_INSPECTION_COMPLETED = "LOCAL_INSPECTION_COMPLETED"
    GUEST_CONSENT_RECORDED = "GUEST_CONSENT_RECORDED"
    DUPLICATE_IGNORED = "DUPLICATE_IGNORED"
    AGENT_CREATED = "AGENT_CREATED"
    CANDIDATES_PROPOSED = "CANDIDATES_PROPOSED"
    STAFF_ACTION = "STAFF_ACTION"
    TICKET_UPDATED = "TICKET_UPDATED"
    HANDLER_ERROR = "HANDLER_ERROR"


@dataclass
class Message:
    message_id: str
    run_id: str
    case_id: str
    sender: str
    receiver: str
    source_node: str
    destination_node: str
    kind: str
    action: str
    correlation_id: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def canonical_bytes(self) -> bytes:
        return canonical_json(self.to_dict())


@dataclass
class Event:
    seq: int
    run_id: str
    case_id: Optional[str]
    step_index: int
    event_type: str
    agent_id: Optional[str] = None
    node_id: Optional[str] = None
    source_node: Optional[str] = None
    destination_node: Optional[str] = None
    message_id: Optional[str] = None
    migration_id: Optional[str] = None
    reason_codes: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PolicyDecision:
    human_required: bool
    decision_source: str
    reason_codes: List[str]
    priority: str
    p_human: float
    threshold: float
    model_recommends_human: bool
    mandatory_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MigrationRecord:
    migration_id: str
    agent_id: str
    case_id: str
    source_node: str
    destination_node: str
    stage: str = MigrationStage.INITIATED.value
    expected_hash: Optional[str] = None
    checkpoint_size: int = 0
    original_bytes: Optional[bytes] = None
    in_transit_bytes: Optional[bytes] = None
    before_snapshot: Optional[Dict[str, Any]] = None
    after_snapshot: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    source_instance_id: Optional[int] = None
    transferred_bytes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        for key in ("original_bytes", "in_transit_bytes"):
            raw = data.get(key)
            data[key] = None if raw is None else {"size": len(raw), "sha256": sha256_hex(raw)}
        data.pop("source_instance_id", None)
        return data


def canonical_json(obj: Any) -> bytes:
    """Serialisasi JSON kanonik untuk checkpoint dan pengukuran byte payload."""
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


class Case:
    """Working state kasus di dalam simulator.

    Setiap perubahan wajib disinkronkan ke tabel `cases` melalui satu method
    repository (``Simulation.sync_case``), bukan dua jalur update terpisah.
    """

    def __init__(
        self,
        case_id: str,
        run_id: str,
        scenario_id: str,
        intent: str,
        flow: str,
        guest_message: str,
        features: Dict[str, Any],
        status: str = CaseStatus.CREATED.value,
        human_required: bool = False,
        human_reason_codes: Optional[List[str]] = None,
        priority: str = "NORMAL",
        p_human: float = 0.0,
        model_recommends_human: bool = False,
        mandatory_reasons: Optional[List[str]] = None,
        decision_source: str = "POLICY_AND_ML",
        reservation_id: str = "RES001",
        original_room_id: str = "R101",
        proposed_room_id: Optional[str] = None,
        proposal_version: int = 0,
        consent: Optional[Dict[str, Any]] = None,
        ticket_ids: Optional[List[str]] = None,
        candidate_rooms: Optional[List[Dict[str, Any]]] = None,
        inspection_results: Optional[List[Dict[str, Any]]] = None,
        evidence: Optional[Dict[str, Any]] = None,
        assigned_room_id: Optional[str] = None,
        closed_note: Optional[str] = None,
        decision_history: Optional[List[Dict[str, Any]]] = None,
        recheck_correlation_id: Optional[str] = None,
        recheck_readiness: Optional[List[Dict[str, Any]]] = None,
        technical_failure: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.case_id = case_id
        self.run_id = run_id
        self.scenario_id = scenario_id
        self.intent = intent
        self.flow = flow
        self.guest_message = guest_message
        self.features = dict(features)
        self.status = status
        self.human_required = human_required
        self.human_reason_codes = list(human_reason_codes or [])
        self.priority = priority
        self.p_human = p_human
        self.model_recommends_human = model_recommends_human
        self.mandatory_reasons = list(mandatory_reasons or [])
        self.decision_source = decision_source
        self.reservation_id = reservation_id
        self.original_room_id = original_room_id
        self.proposed_room_id = proposed_room_id
        self.proposal_version = proposal_version
        self.consent = consent
        self.ticket_ids = list(ticket_ids or [])
        self.candidate_rooms = list(candidate_rooms or [])
        self.inspection_results = list(inspection_results or [])
        self.evidence = dict(evidence or {})
        self.assigned_room_id = assigned_room_id
        self.closed_note = closed_note
        self.decision_history = list(decision_history or [])
        self.recheck_correlation_id = recheck_correlation_id
        self.recheck_readiness = list(recheck_readiness or [])
        self.technical_failure = technical_failure

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "intent": self.intent,
            "flow": self.flow,
            "guest_message": self.guest_message,
            "features": self.features,
            "status": self.status,
            "human_required": self.human_required,
            "human_reason_codes": self.human_reason_codes,
            "priority": self.priority,
            "p_human": self.p_human,
            "model_recommends_human": self.model_recommends_human,
            "mandatory_reasons": self.mandatory_reasons,
            "decision_source": self.decision_source,
            "reservation_id": self.reservation_id,
            "original_room_id": self.original_room_id,
            "proposed_room_id": self.proposed_room_id,
            "proposal_version": self.proposal_version,
            "consent": self.consent,
            "ticket_ids": self.ticket_ids,
            "candidate_rooms": self.candidate_rooms,
            "inspection_results": self.inspection_results,
            "evidence": self.evidence,
            "assigned_room_id": self.assigned_room_id,
            "closed_note": self.closed_note,
            "decision_history": self.decision_history,
            "recheck_correlation_id": self.recheck_correlation_id,
            "recheck_readiness": self.recheck_readiness,
            "technical_failure": self.technical_failure,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Case":
        payload = dict(data)
        case_id = payload.pop("case_id")
        return cls(case_id=case_id, **payload)
