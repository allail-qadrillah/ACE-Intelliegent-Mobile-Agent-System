"""Scenario Scout: titik masuk kasus.

Mengubah fixture skenario (keluhan tamu yang sudah terstruktur) menjadi pesan
``START_CASE`` untuk Orchestrator. Tidak ada NLP; scout hanya pengirim.
"""

from __future__ import annotations

from typing import Any, Dict

from ..models import Action, EventType, Message, MessageKind, NodeId
from .base import BaseAgent


class ScenarioScoutAgent(BaseAgent):
    """Scout: membentuk request terstruktur dari fixture (tanpa NLP)."""

    capability_key = "scenario_scout"

    def __init__(self, node_id: str = NodeId.FRONT_OFFICE.value) -> None:
        super().__init__("scenario_scout", node_id)

    def build_start_message(self, scenario: Dict[str, Any], run_id: str) -> Message:
        """Bungkus data skenario menjadi pesan pertama yang memulai kasus."""
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
        # Scout tidak pernah menerima pesan; jika terjadi, catat sebagai error.
        sim.emit(
            EventType.HANDLER_ERROR.value,
            agent_id=self.agent_id,
            node_id=self.node_id,
            details={"reason": "SCOUT_IS_SENDER_ONLY"},
        )
