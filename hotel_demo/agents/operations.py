"""Operations Agent (node Operations): pemilik data tiket & kesiapan kamar.

Aksi yang ditangani:
- ``CREATE_TICKET``: buat tiket maintenance/housekeeping (idempoten);
- ``GET_READINESS``: baca status kesiapan kamar (dipakai recheck sebelum commit);
- ``INSPECT_CANDIDATES``: inspeksi batch untuk mode baseline statis.
"""

from __future__ import annotations

from typing import Any

from ..models import Action, EventType, Message, MessageKind, NodeId
from .base import BaseAgent
from .inspection import evaluate_candidates


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
        """Buat tiket kerja; ``operation_key`` mencegah tiket ganda."""
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
        """Baca readiness terbaru untuk daftar kamar lalu balas ``READINESS_RESULT``."""
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
        # 1. Pastikan pemanggil memang berhak meminta inspeksi.
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

        # 2. Baca data readiness lokal untuk semua kandidat.
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

        # 3. Jalankan kernel penilaian dan kirim hasilnya balik.
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
