"""AC-01, AC-07 s/d AC-11, AC-13 s/d AC-15, AC-24 s/d AC-29: skenario end-to-end."""

from __future__ import annotations

import json
import socket

import pytest

from hotel_demo import ml
from hotel_demo.evaluation import run_comparison
from hotel_demo.simulation import Simulation


def test_s01_inspection_rejects_dirty_and_proposes_r103(run_scenario):
    simulation = run_scenario("S01")
    case = simulation.case

    assert case.status == "WAITING_GUEST"
    assert case.proposed_room_id == "R103"
    assert case.proposal_version == 1
    results = {item["room_id"]: item for item in case.inspection_results}
    assert results["R102"]["is_routine_eligible"] is False
    assert "DIRTY" in results["R102"]["reason_codes"]
    assert results["R103"]["is_routine_eligible"] is True
    assert "READY_EQUAL_ROOM" in results["R103"]["reason_codes"]
    # Belum ada perubahan DB sebelum consent.
    assert simulation.front_office.get_reservation("RES001")["reservation"]["room_id"] == "R101"
    assert simulation.front_office.get_room("R103")["room"]["occupied_by"] is None
    assert len(simulation.list_tickets()) == 1


def test_s01_consent_commits_room_change_atomically(run_scenario):
    simulation = run_scenario("S01", accept=True)
    case = simulation.case

    assert case.status == "DIGITAL_COMPLETED"
    assert case.assigned_room_id == "R103"
    reservation = simulation.front_office.get_reservation("RES001")["reservation"]
    assert reservation["room_id"] == "R103"
    assert reservation["nightly_rate"] == 500000
    assert simulation.front_office.get_room("R101")["room"]["occupied_by"] is None
    assert simulation.front_office.get_room("R103")["room"]["occupied_by"] == "RES001"
    assert simulation.front_office.get_folio("RES001")["total"] == 650000

    tickets = simulation.list_tickets()
    assert len(tickets) == 1
    assert tickets[0]["department"] == "MAINTENANCE"
    assert tickets[0]["status"] == "PENDING"

    # Investigator tetap di Operations dan diarsipkan setelah DONE.
    assert simulation.owner_by_agent["MA-001"] is None
    assert simulation.active_instance_count("MA-001") == 0
    assert simulation.archived["MA-001"]["status"] == "DONE"
    assert simulation.archived["MA-001"]["node_id"] == "OPERATIONS"
    assert simulation.metrics["migrations_succeeded"] == 1


def test_s01_decline_keeps_reservation_and_ticket(run_scenario):
    simulation = run_scenario("S01", accept=False)
    case = simulation.case

    assert case.status == "CLOSED_GUEST_DECLINED"
    assert simulation.front_office.get_reservation("RES001")["reservation"]["room_id"] == "R101"
    assert simulation.front_office.get_room("R103")["room"]["occupied_by"] is None
    tickets = simulation.list_tickets()
    assert len(tickets) == 1 and tickets[0]["status"] == "PENDING"


def test_s01_stale_room_state_escalates_to_human(run_scenario):
    simulation = run_scenario("S01")
    assert simulation.case.status == "WAITING_GUEST"

    # Fixture konflik: kamar target berubah setelah proposal, sebelum consent.
    simulation.front_office.conn.execute(
        "UPDATE rooms SET version = version + 1 WHERE id = 'R103'"
    )
    simulation.submit_guest_choice(True)
    simulation.run_until_pause()

    case = simulation.case
    assert case.status == "WAITING_HUMAN"
    assert "STALE_ROOM_STATE" in case.human_reason_codes
    assert case.human_required is True
    assert simulation.front_office.get_reservation("RES001")["reservation"]["room_id"] == "R101"
    assert simulation.front_office.get_room("R103")["room"]["occupied_by"] is None
    assert simulation.front_office.get_room("R101")["room"]["occupied_by"] == "RES001"


def test_s01_stale_readiness_escalates_to_human(run_scenario):
    simulation = run_scenario("S01")
    simulation.operations.set_maintenance_block("R103", True)
    simulation.submit_guest_choice(True)
    simulation.run_until_pause()

    assert simulation.case.status == "WAITING_HUMAN"
    assert "STALE_ROOM_STATE" in simulation.case.human_reason_codes
    assert simulation.front_office.get_reservation("RES001")["reservation"]["room_id"] == "R101"


def test_s02_gathers_evidence_then_waits_for_staff(run_scenario):
    simulation = run_scenario("S02")
    case = simulation.case

    assert case.status == "WAITING_HUMAN"
    assert case.human_required is True
    assert case.decision_source == "POLICY"
    assert "UPGRADE_REQUIRES_HUMAN" in case.human_reason_codes
    assert simulation.metrics["migrations_succeeded"] == 1

    results = {item["room_id"]: item for item in case.inspection_results}
    assert list(results) == ["R201"]
    assert results["R201"]["is_ready"] is True
    assert results["R201"]["is_routine_eligible"] is False
    assert "UPGRADE_REQUIRES_HUMAN" in results["R201"]["reason_codes"]

    # Tidak ada perubahan kamar/tarif/folio.
    assert simulation.front_office.get_reservation("RES001")["reservation"]["room_id"] == "R101"
    assert simulation.front_office.get_reservation("RES001")["reservation"]["nightly_rate"] == 500000
    assert simulation.front_office.get_folio("RES001")["total"] == 650000
    assert len(simulation.list_tickets()) == 1
    assert case.proposed_room_id is None


def test_s02_candidates_are_only_upgrade_alternatives(run_scenario):
    simulation = run_scenario("S02")
    candidates = [item["room_id"] for item in simulation.case.candidate_rooms]
    assert candidates == ["R201"]
    assert simulation.front_office.get_room("R102")["room"]["occupied_by"] == "RESD01"
    assert simulation.front_office.get_room("R103")["room"]["occupied_by"] == "RESD02"


def test_s04_answers_check_in_faq(run_scenario):
    simulation = run_scenario("S04")
    case = simulation.case
    assert case.status == "DIGITAL_COMPLETED"
    assert case.evidence["faq"]["answer"] == "Waktu check-in Hotel Nusantara Demo mulai pukul 14.00."
    assert simulation.list_tickets() == []
    assert simulation.metrics["migrations_succeeded"] == 0
    assert simulation.metrics["inter_node_messages"] == 0


def test_s05_housekeeping_ticket_flow(run_scenario):
    simulation = run_scenario("S05")
    case = simulation.case
    assert case.status == "DIGITAL_COMPLETED"
    assert case.human_required is False
    tickets = simulation.list_tickets()
    assert len(tickets) == 1
    assert tickets[0]["department"] == "HOUSEKEEPING"
    assert tickets[0]["status"] == "PENDING"

    ticket_id = tickets[0]["id"]
    assert simulation.staff_update_ticket(ticket_id, "DONE")["ok"] is False
    assert simulation.staff_update_ticket(ticket_id, "IN_PROGRESS")["ok"] is True
    assert simulation.staff_update_ticket(ticket_id, "DONE")["ok"] is True
    assert simulation.list_tickets()[0]["status"] == "DONE"
    assert simulation.metrics["migrations_succeeded"] == 0


def test_s06_shows_billing_details(run_scenario):
    simulation = run_scenario("S06")
    case = simulation.case
    assert case.status == "DIGITAL_COMPLETED"
    folio = case.evidence["folio"]
    assert [entry["id"] for entry in folio["entries"]] == ["F01", "F02"]
    assert folio["total"] == 650000
    assert simulation.metrics["migrations_succeeded"] == 0
    assert simulation.front_office.get_folio("RES001")["total"] == 650000


def test_read_only_render_does_not_change_state(run_scenario):
    simulation = run_scenario("S01")
    before_metrics = dict(simulation.metrics)
    before_status = simulation.case.status
    before_events = len(simulation.events)

    for _ in range(5):
        snapshot = simulation.snapshot()
        assert snapshot["case"]["status"] == before_status

    assert dict(simulation.metrics) == before_metrics
    assert len(simulation.events) == before_events
    assert simulation.front_office.get_reservation("RES001")["reservation"]["room_id"] == "R101"


def test_reset_creates_fresh_run(make_sim):
    first = make_sim("S01")
    first.start_scenario()
    first.run_until_pause()
    first.submit_guest_choice(True)
    first.run_until_pause()
    assert first.case.status == "DIGITAL_COMPLETED"
    assert first.front_office.get_reservation("RES001")["reservation"]["room_id"] == "R103"

    second = make_sim("S01")
    second.start_scenario()
    assert second.case is None
    assert second.metrics["messages_sent"] == 1
    assert second.owner_by_agent.get("MA-001") is None
    assert "MA-001" not in second.agents
    assert second.run_id != first.run_id
    assert second.front_office.get_reservation("RES001")["reservation"]["room_id"] == "R101"
    assert second.front_office.get_room("R103")["room"]["occupied_by"] is None
    assert second.front_office.get_folio("RES001")["total"] == 650000


def test_two_simulators_are_isolated(make_sim):
    first = make_sim("S01")
    first.start_scenario()
    first.run_until_pause()
    first.submit_guest_choice(True)
    first.run_until_pause()

    second = make_sim("S01")
    second.start_scenario()
    second.run_until_pause()

    assert first.front_office.get_reservation("RES001")["reservation"]["room_id"] == "R103"
    assert second.front_office.get_reservation("RES001")["reservation"]["room_id"] == "R101"
    assert second.front_office.get_room("R103")["room"]["occupied_by"] is None
    assert second.case.status == "WAITING_GUEST"


def test_export_is_readable_and_complete(run_scenario):
    simulation = run_scenario("S01", accept=True)
    payload = json.loads(simulation.export_json())

    assert payload["metadata"]["run_id"] == simulation.run_id
    assert payload["metadata"]["scenario_id"] == "S01"
    assert payload["metadata"]["mode"] == "mobile"
    assert payload["metadata"]["model"]["dataset"]["n_total"] == 48
    assert payload["case"]["status"] == "DIGITAL_COMPLETED"
    assert payload["metrics"]["migrations_succeeded"] == 1
    assert payload["checkpoints"]["last_migration"]["stage"] == "SUCCEEDED"
    assert payload["databases"]["front_office"]["reservations"]
    assert payload["databases"]["operations"]["tickets"]
    assert payload["events"]
    assert payload["messages"]
    assert (
        payload["metrics"]["total_simulated_payload_bytes"]
        == payload["metrics"]["inter_node_message_bytes"]
        + payload["metrics"]["transferred_checkpoint_bytes"]
    )


def test_core_scenarios_run_without_network(monkeypatch, make_sim):
    """AC-29: engine, ML, dan evaluasi tetap berjalan tanpa koneksi keluar."""

    def blocked(*args, **kwargs):
        raise AssertionError("Koneksi jaringan tidak diizinkan pada core scenario.")

    monkeypatch.setattr(socket.socket, "connect", blocked, raising=True)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked, raising=True)
    monkeypatch.setattr(socket, "create_connection", blocked, raising=True)

    trained = ml.train()
    assert trained.report["dataset"]["n_total"] == 48

    for scenario_id, expected in (
        ("S01", "WAITING_GUEST"),
        ("S04", "DIGITAL_COMPLETED"),
    ):
        simulation = make_sim(scenario_id)
        simulation.start_scenario()
        simulation.run_until_pause()
        assert simulation.case.status == expected

    result = run_comparison(model=trained)
    assert all(item["passed"] for item in result["assertions"])


def test_run_until_pause_reports_loop_limit(run_scenario):
    simulation = run_scenario("S01")
    # Tidak ada pekerjaan tertunda: run_until_pause harus langsung selesai.
    assert simulation.run_until_pause() == 0
