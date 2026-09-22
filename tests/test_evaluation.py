"""AC-23 dan AC-27: perbandingan setara dan isolasi run evaluasi."""

from __future__ import annotations

from hotel_demo.evaluation import comparison_table_rows, run_comparison


def test_comparison_business_outcomes_are_equivalent(model):
    result = run_comparison(model=model)
    assertions = result["assertions"]
    assert assertions
    failed = [item for item in assertions if not item["passed"]]
    assert not failed, failed

    runs = {(run["scenario_id"], run["mode"]): run for run in result["runs"]}
    assert runs[("S01", "mobile")]["assigned_room_id"] == "R103"
    assert runs[("S01", "static")]["assigned_room_id"] == "R103"
    assert runs[("S02", "mobile")]["assigned_room_id"] == "R101"
    assert runs[("S02", "static")]["assigned_room_id"] == "R101"

    assert runs[("S01", "static")]["migrations_succeeded"] == 0
    assert runs[("S01", "mobile")]["migrations_succeeded"] == 1
    assert runs[("S01", "mobile")]["checkpoint_bytes"] > 0
    assert runs[("S01", "static")]["checkpoint_bytes"] == 0
    assert runs[("S02", "static")]["migrations_succeeded"] == 0
    assert runs[("S02", "mobile")]["migrations_succeeded"] == 1

    assert all(run["duplicate_side_effects"] == 0 for run in result["runs"])
    assert runs[("S01", "mobile")]["status"] == "DIGITAL_COMPLETED"
    assert runs[("S02", "mobile")]["status"] == "WAITING_HUMAN"


def test_comparison_table_has_expected_columns(model):
    rows = comparison_table_rows(run_comparison(model=model))
    assert len(rows) == 4
    assert {"Skenario", "Mode", "Status", "Kamar akhir", "Tiket", "Pesan", "Byte checkpoint"} <= set(
        rows[0]
    )


def test_evaluation_does_not_touch_active_run(model, make_sim):
    active = make_sim("S01")
    active.start_scenario()
    active.run_until_pause()
    before = dict(active.metrics)
    before_status = active.case.status

    run_comparison(model=model)

    assert dict(active.metrics) == before
    assert active.case.status == before_status
    assert active.front_office.get_reservation("RES001")["reservation"]["room_id"] == "R101"
