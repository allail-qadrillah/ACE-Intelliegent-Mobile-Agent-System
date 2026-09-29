"""Concierge Agent (node Front Office): menjawab FAQ hotel dari basis data lokal."""

from __future__ import annotations

from typing import Any

from ..models import Action, EventType, Message, MessageKind, NodeId
from .base import BaseAgent


class ConciergeAgent(BaseAgent):
    capability_key = "concierge"

    def __init__(self, node_id: str = NodeId.FRONT_OFFICE.value) -> None:
        super().__init__("concierge", node_id)

    def handle(self, message: Message, sim: Any) -> None:
        """``GET_FAQ`` → cari jawaban berdasarkan key → balas ``FAQ_RESULT``."""
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
