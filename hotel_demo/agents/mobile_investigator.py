"""Mobile Investigator: agen yang "berpindah" ke node tempat data berada.

Identitasnya tetap (``MA-001``), tapi instance aktifnya dipindah dari
Front Office ke Operations lewat checkpoint JSON (lihat ``migration.py``).

Siklus phase pada mode mobile::

    CREATED --INSPECT_CANDIDATES--> INSPECT_LOCAL (suspend, migrasi)
            --tiba di Operations--> jalankan kernel --> REPORT_RESULT --> DONE

Pada mode statis (baseline) agen tidak migrasi; ia mendelegasikan inspeksi
batch ke ``OperationsAgent`` lalu meneruskan hasilnya ke Orchestrator.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..models import (
    Action,
    AgentPhase,
    AgentRuntimeStatus,
    EventType,
    Message,
    NodeId,
)
from .base import BaseAgent
from .inspection import evaluate_candidates


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

    # -------------------------------------------------------------- checkpoint
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
        """Bangun ulang agen di node tujuan dari data checkpoint."""
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
        """Perintah inspeksi. Perilakunya tergantung phase & node saat ini."""
        # Masih di Front Office: simpan tugas, lalu migrasi (mobile) atau delegasi (statis).
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

        # Sudah tiba di Operations setelah migrasi: inspeksi data lokal.
        if self.phase == AgentPhase.INSPECT_LOCAL.value and self.node_id == NodeId.OPERATIONS.value:
            self._run_local_kernel(sim)
            return

        sim.emit(
            EventType.HANDLER_ERROR.value,
            agent_id=self.agent_id,
            node_id=self.node_id,
            details={"reason": "INSPECT_WRONG_PHASE", "phase": self.phase},
        )

    # ------------------------------------------------------------- mode mobile
    def _start_mobile(self, sim: Any) -> None:
        # Tetapkan phase kelanjutan SEBELUM serialisasi.
        self.phase = AgentPhase.INSPECT_LOCAL.value
        self.status = AgentRuntimeStatus.SUSPENDED.value
        self.last_action = "MIGRATE_TO_OPERATIONS"
        sim.begin_migration(self.agent_id, NodeId.OPERATIONS.value)

    def _run_local_kernel(self, sim: Any) -> None:
        """Di node Operations: baca readiness lokal, nilai kandidat, lapor ke Orchestrator."""
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
        # Tugas selesai: agen diarsipkan.
        self.phase = AgentPhase.DONE.value
        self.status = AgentRuntimeStatus.DONE.value
        sim.archive_agent(self.agent_id)

    # ------------------------------------------------------ mode statis (baseline)
    def _start_static(self, sim: Any) -> None:
        """Tanpa migrasi: minta OperationsAgent menjalankan inspeksi batch."""
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
        """Hasil batch dari OperationsAgent: teruskan ke Orchestrator lalu selesai."""
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
