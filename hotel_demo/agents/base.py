"""Fondasi semua agen: tabel capability dan class ``BaseAgent``."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..models import AgentPhase, AgentRuntimeStatus, Message, NodeId

# Capability = daftar "izin" tool yang boleh dipakai tiap jenis agen.
# Ditentukan konfigurasi runtime berdasarkan jenis agen terdaftar,
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

# Jenis data yang tersimpan di tiap node. Data readiness kamar hanya ada di
# node Operations, itulah alasan MobileInvestigator perlu bermigrasi ke sana.
DATA_CAPABILITIES: Dict[str, set] = {
    NodeId.FRONT_OFFICE.value: {"reservation", "folio", "faq"},
    NodeId.OPERATIONS.value: {"readiness", "ticket"},
}


class BaseAgent:
    """Kerangka umum agen: identitas, lokasi node, status, dan capability.

    Subclass cukup mengisi ``capability_key`` dan meng-override ``handle``.
    """

    capability_key = ""

    def __init__(self, agent_id: str, node_id: str, case_id: Optional[str] = None) -> None:
        self.agent_id = agent_id
        self.node_id = node_id  # node tempat agen sedang berjalan
        self.status = AgentRuntimeStatus.ACTIVE.value
        self.phase = AgentPhase.CREATED.value
        self.case_id = case_id
        self.last_action: Optional[str] = None  # aksi terakhir, untuk ditampilkan di UI

    @property
    def agent_type(self) -> str:
        return "static"

    @property
    def capabilities(self) -> tuple:
        return CAPABILITIES.get(self.capability_key, ())

    def state_snapshot(self) -> Dict[str, Any]:
        """Ringkasan state agen untuk UI/log."""
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
        """Proses satu pesan masuk. ``sim`` adalah Simulation (antrian, repo, event)."""
        raise NotImplementedError
