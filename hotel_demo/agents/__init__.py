"""Paket agen: static agents, orchestrator, dan mobile investigator.

Setiap agen adalah class Python kecil dengan ``handle(message, sim)``. Keputusan
berbasis rules/state machine; tidak ada LLM.

Peta file (satu agen per file):

- ``base.py``                — ``BaseAgent`` + tabel capability per agen & per node
- ``inspection.py``          — ``evaluate_candidates``: kernel murni penilaian kamar
- ``scenario_scout.py``      — ``ScenarioScoutAgent``: mengubah skenario jadi pesan awal
- ``orchestrator.py``        — ``OrchestratorAgent``: "otak" alur kasus (triase → selesai)
- ``reservation.py``         — ``ReservationAgent``: cari kandidat kamar & commit pindah kamar
- ``billing.py``             — ``BillingAgent``: ambil folio/tagihan tamu
- ``concierge.py``           — ``ConciergeAgent``: jawab FAQ hotel
- ``operations.py``          — ``OperationsAgent``: tiket & data kesiapan kamar (node Operations)
- ``mobile_investigator.py`` — ``MobileInvestigator``: agen yang bermigrasi ke node Operations

Semua nama di-export ulang di sini sehingga ``from .agents import X`` tetap berlaku.
"""

from .base import CAPABILITIES, DATA_CAPABILITIES, BaseAgent
from .billing import BillingAgent
from .concierge import ConciergeAgent
from .inspection import evaluate_candidates
from .mobile_investigator import MobileInvestigator
from .operations import OperationsAgent
from .orchestrator import OrchestratorAgent
from .reservation import ReservationAgent
from .scenario_scout import ScenarioScoutAgent

__all__ = [
    "CAPABILITIES",
    "DATA_CAPABILITIES",
    "BaseAgent",
    "evaluate_candidates",
    "ScenarioScoutAgent",
    "OrchestratorAgent",
    "ReservationAgent",
    "BillingAgent",
    "ConciergeAgent",
    "OperationsAgent",
    "MobileInvestigator",
]
