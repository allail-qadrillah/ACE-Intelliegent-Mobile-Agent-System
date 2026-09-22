"""Evaluasi setara: perbandingan jalur mobile dan baseline statis.

Menjalankan simulator baru yang terisolasi sehingga tidak mengubah run aktif.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .simulation import Simulation

COMPARISON_SCENARIOS = ("S01", "S02")
COMPARISON_MODES = ("mobile", "static")


def run_single(
    *,
    scenario_id: str,
    mode: str,
    model: Any,
    seed_path: Optional[Path] = None,
    scenarios_path: Optional[Path] = None,
    threshold: float = 0.80,
) -> Dict[str, Any]:
    simulation = Simulation(
        mode=mode,
        scenario_id=scenario_id,
        model=model,
        seed_path=seed_path,
        scenarios_path=scenarios_path,
        threshold=threshold,
        enable_audit=False,
    )
    try:
        simulation.start_scenario()
        simulation.run_until_pause()
        # Harness evaluasi memberi consent otomatis khusus S01.
        if (
            scenario_id == "S01"
            and simulation.case is not None
            and simulation.case.status == "WAITING_GUEST"
        ):
            simulation.submit_guest_choice(True, actor="EVALUATION_GUEST")
            simulation.run_until_pause()
        return _summarize(simulation)
    finally:
        simulation.close()


def _summarize(simulation: Simulation) -> Dict[str, Any]:
    case = simulation.case
    folio = simulation.front_office.get_folio("RES001")
    reservation = simulation.front_office.get_reservation("RES001")
    metrics = simulation.metrics
    tickets = simulation.list_tickets()
    return {
        "scenario_id": simulation.scenario_id,
        "mode": simulation.mode,
        "status": None if case is None else case.status,
        "human_required": bool(case.human_required) if case else False,
        "human_reason_codes": list(case.human_reason_codes) if case else [],
        "decision_source": None if case is None else case.decision_source,
        "p_human": None if case is None else case.p_human,
        "original_room_id": None if case is None else case.original_room_id,
        "assigned_room_id": None if case is None else (case.assigned_room_id or reservation["reservation"]["room_id"]),
        "proposed_room_id": None if case is None else case.proposed_room_id,
        "inspection_results": [] if case is None else case.inspection_results,
        "feasible_rooms": [] if case is None else case.evidence.get("feasible_rooms", []),
        "ticket_count": len(tickets),
        "ticket_statuses": [ticket["status"] for ticket in tickets],
        "messages_sent": metrics["messages_sent"],
        "inter_node_messages": metrics["inter_node_messages"],
        "checkpoint_bytes": metrics["transferred_checkpoint_bytes"],
        "total_simulated_payload_bytes": metrics["inter_node_message_bytes"]
        + metrics["transferred_checkpoint_bytes"],
        "engine_steps": metrics["engine_steps"],
        "engine_compute_ms": round(metrics["engine_compute_ms"], 3),
        "migrations_succeeded": metrics["migrations_succeeded"],
        "migrations_failed": metrics["migrations_failed"],
        "duplicate_side_effects": metrics["duplicate_side_effects"],
        "nightly_rate": reservation["reservation"]["nightly_rate"] if reservation["ok"] else None,
        "folio_total": folio["total"] if folio["ok"] else None,
    }


def run_comparison(
    *,
    model: Any,
    seed_path: Optional[Path] = None,
    scenarios_path: Optional[Path] = None,
    threshold: float = 0.80,
) -> Dict[str, Any]:
    runs: List[Dict[str, Any]] = []
    for scenario_id in COMPARISON_SCENARIOS:
        for mode in COMPARISON_MODES:
            runs.append(
                run_single(
                    scenario_id=scenario_id,
                    mode=mode,
                    model=model,
                    seed_path=seed_path,
                    scenarios_path=scenarios_path,
                    threshold=threshold,
                )
            )
    return {"runs": runs, "assertions": _assert_equivalence(runs)}


def _by_key(runs: List[Dict[str, Any]], scenario_id: str, mode: str) -> Dict[str, Any]:
    for run in runs:
        if run["scenario_id"] == scenario_id and run["mode"] == mode:
            return run
    raise KeyError(f"Run {scenario_id}/{mode} tidak ditemukan.")


def _assert_equivalence(runs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    assertions: List[Dict[str, Any]] = []

    def check(name: str, condition: bool, detail: str) -> None:
        assertions.append({"name": name, "passed": bool(condition), "detail": detail})

    for scenario_id in COMPARISON_SCENARIOS:
        mobile = _by_key(runs, scenario_id, "mobile")
        static = _by_key(runs, scenario_id, "static")
        check(
            f"{scenario_id} status setara",
            mobile["status"] == static["status"],
            f"mobile={mobile['status']} static={static['status']}",
        )
        check(
            f"{scenario_id} room akhir setara",
            mobile["assigned_room_id"] == static["assigned_room_id"],
            f"mobile={mobile['assigned_room_id']} static={static['assigned_room_id']}",
        )
        check(
            f"{scenario_id} hasil inspeksi setara",
            [
                (item["room_id"], item["is_routine_eligible"], tuple(item["reason_codes"]))
                for item in mobile["inspection_results"]
            ]
            == [
                (item["room_id"], item["is_routine_eligible"], tuple(item["reason_codes"]))
                for item in static["inspection_results"]
            ],
            "kernel sama pada kedua jalur",
        )
        check(
            f"{scenario_id} jumlah tiket setara",
            mobile["ticket_count"] == static["ticket_count"],
            f"mobile={mobile['ticket_count']} static={static['ticket_count']}",
        )
        check(
            f"{scenario_id} static nol migrasi",
            static["migrations_succeeded"] == 0,
            f"static migrations={static['migrations_succeeded']}",
        )
        check(
            f"{scenario_id} mobile satu migrasi",
            mobile["migrations_succeeded"] == 1,
            f"mobile migrations={mobile['migrations_succeeded']}",
        )
        check(
            f"{scenario_id} tarif tidak berubah",
            mobile["nightly_rate"] == static["nightly_rate"] == 500000
            and mobile["folio_total"] == static["folio_total"] == 650000,
            f"rate={mobile['nightly_rate']}/{static['nightly_rate']} folio={mobile['folio_total']}/{static['folio_total']}",
        )

    s01_mobile = _by_key(runs, "S01", "mobile")
    check(
        "S01 kamar akhir R103",
        s01_mobile["assigned_room_id"] == "R103",
        f"assigned={s01_mobile['assigned_room_id']}",
    )
    check("S01 satu tiket", s01_mobile["ticket_count"] == 1, f"tickets={s01_mobile['ticket_count']}")
    check(
        "S01 selesai digital",
        s01_mobile["status"] == "DIGITAL_COMPLETED",
        f"status={s01_mobile['status']}",
    )

    s02_mobile = _by_key(runs, "S02", "mobile")
    check("S02 kamar tetap R101", s02_mobile["assigned_room_id"] == "R101", f"assigned={s02_mobile['assigned_room_id']}")
    check("S02 satu tiket", s02_mobile["ticket_count"] == 1, f"tickets={s02_mobile['ticket_count']}")
    check(
        "S02 wajib review staf",
        s02_mobile["status"] == "WAITING_HUMAN" and s02_mobile["human_required"],
        f"status={s02_mobile['status']} human_required={s02_mobile['human_required']}",
    )
    return assertions


def comparison_table_rows(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for run in result["runs"]:
        rows.append(
            {
                "Skenario": run["scenario_id"],
                "Mode": run["mode"],
                "Status": run["status"],
                "Kamar akhir": run["assigned_room_id"],
                "Inspeksi": ", ".join(
                    f"{item['room_id']}={'rutin' if item['is_routine_eligible'] else 'tolak'}"
                    for item in run["inspection_results"]
                ),
                "Tiket": run["ticket_count"],
                "Pesan": run["messages_sent"],
                "Pesan antar-node": run["inter_node_messages"],
                "Byte checkpoint": run["checkpoint_bytes"],
                "Total payload": run["total_simulated_payload_bytes"],
                "Step": run["engine_steps"],
                "Compute (ms)": run["engine_compute_ms"],
                "Migrasi": run["migrations_succeeded"],
            }
        )
    return rows
