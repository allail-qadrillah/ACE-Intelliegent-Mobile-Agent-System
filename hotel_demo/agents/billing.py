"""Billing Agent (node Front Office): mengambil folio (rincian tagihan) tamu."""

from __future__ import annotations

from typing import Any

from ..models import Action, EventType, Message, MessageKind, NodeId
from .base import BaseAgent


class BillingAgent(BaseAgent):
    capability_key = "billing"

    def __init__(self, node_id: str = NodeId.FRONT_OFFICE.value) -> None:
        super().__init__("billing", node_id)

    def handle(self, message: Message, sim: Any) -> None:
        """``GET_FOLIO`` → baca folio reservasi → balas ``FOLIO_RESULT``."""
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
