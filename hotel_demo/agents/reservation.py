"""Reservation Agent (node Front Office).

Menangani dua aksi:
- ``FIND_ROOM_CANDIDATES``: cari kamar pengganti untuk suatu reservasi;
- ``COMMIT_ROOM_CHANGE``: eksekusi pindah kamar (dengan cek versi & consent).
"""

from __future__ import annotations

from typing import Any

from ..models import Action, EventType, Message, MessageKind, NodeId
from .base import BaseAgent


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
        """Ambil daftar kamar kandidat dari repo lalu balas ``CANDIDATES_FOUND``."""
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
        """Commit pindah kamar. Repo menolak jika versi data berubah, consent tidak ada,
        atau hasil recheck readiness tidak cocok (lihat ``repository.commit_room_change``).
        """
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
