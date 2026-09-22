"""AC-12, AC-18, AC-19, AC-20: policy wajib, eskalasi, dan pengambilalihan staf."""

from __future__ import annotations

import pytest

from hotel_demo import policy
from hotel_demo.simulation import Simulation

MANDATORY_FLAGS = (
    "emergency",
    "request_human",
    "financial_dispute",
    "compensation_requested",
    "upgrade_exception",
)


@pytest.mark.parametrize("flag", MANDATORY_FLAGS)
def test_mandatory_flag_beats_low_probability(flag):
    decision = policy.evaluate_case({flag: True}, 0.01)
    assert decision.human_required is True
    assert decision.decision_source == "POLICY"
    assert decision.reason_codes
    assert decision.model_recommends_human is False


def test_emergency_sets_urgent_priority():
    decision = policy.evaluate_case({"emergency": True}, 0.01)
    assert decision.priority == "URGENT"


def test_ml_only_review_above_threshold():
    decision = policy.evaluate_case({}, 0.99)
    assert decision.human_required is True
    assert decision.decision_source == "ML"
    assert decision.model_recommends_human is True


def test_allow_below_threshold_without_flags():
    decision = policy.evaluate_case({}, 0.01)
    assert decision.human_required is False
    assert decision.decision_source == "POLICY_AND_ML"
    assert decision.reason_codes == []


def test_threshold_is_inclusive():
    decision = policy.evaluate_case({}, 0.80)
    assert decision.human_required is True


def test_validate_room_change_reports_stale_and_policy_codes():
    codes = policy.validate_room_change(
        policy_decision={"human_required": False},
        consent={"accepted": True, "case_id": "CASE-001", "proposed_room_id": "R103", "proposal_version": 1},
        case={"case_id": "CASE-001", "proposal_version": 1},
        reservation={"id": "RES001", "room_id": "R101", "room_type": "standard", "nightly_rate": 500000, "status": "checked_in", "version": 2},
        target_room={"id": "R103", "room_type": "standard", "nightly_rate": 500000, "occupied_by": "RESX", "version": 3},
        original_room={"id": "R101", "version": 2},
        fresh_readiness={"cleanliness": "dirty", "maintenance_blocked": True, "evidence_version": 9},
        expected_versions={"reservation": 1, "original_room": 1, "room": 1, "readiness": 1},
        recheck_correlation_id="RECHECK-CASE-001",
        expected_recheck_correlation="RECHECK-CASE-001",
    )
    assert "ROOM_OCCUPIED" in codes
    assert "STALE_ROOM_STATE" in codes
    assert "NOT_READY" in codes
    assert "MAINTENANCE_BLOCKED" in codes
    assert policy.summarize_commit_refusal(codes) == "STALE_ROOM_STATE"


def test_s03_mandatory_escalation_with_low_stub(stub_model_factory):
    simulation = Simulation(mode="mobile", scenario_id="S03", model=stub_model_factory(0.01))
    try:
        simulation.start_scenario()
        simulation.run_until_pause()
        case = simulation.case
        assert case.human_required is True
        assert case.decision_source == "POLICY"
        assert "FINANCIAL_DISPUTE" in case.human_reason_codes
        assert case.status == "WAITING_HUMAN"
        assert case.p_human == pytest.approx(0.01)

        folio = simulation.front_office.get_folio("RES001")
        assert [entry["id"] for entry in folio["entries"]] == ["F01", "F02"]
        assert folio["total"] == 650000

        assert "MA-001" not in simulation.agents
        assert simulation.metrics["migrations_succeeded"] == 0
        assert simulation.metrics["messages_sent"] == 3
    finally:
        simulation.close()


def test_staff_takeover_then_close_requires_note(stub_model_factory):
    simulation = Simulation(mode="mobile", scenario_id="S03", model=stub_model_factory(0.01))
    try:
        simulation.start_scenario()
        simulation.run_until_pause()
        assert simulation.staff_close_case("")["ok"] is False
        assert simulation.staff_take_over()["ok"] is True
        assert simulation.case.status == "HUMAN_HANDLING"
        assert simulation.staff_close_case("   ")["ok"] is False
        assert simulation.staff_close_case("Tamu diberi penjelasan; tagihan ditinjau manual.")["ok"] is True
        assert simulation.case.status == "CLOSED_BY_STAFF"
        assert simulation.case.closed_note

        # Menutup kasus tidak mengubah tagihan/reservasi dan tidak menutup tiket.
        folio = simulation.front_office.get_folio("RES001")
        assert folio["total"] == 650000
        assert simulation.list_tickets() == []
        assert simulation.front_office.get_reservation("RES001")["reservation"]["room_id"] == "R101"
    finally:
        simulation.close()


def test_staff_takeover_requires_waiting_human(stub_model_factory):
    simulation = Simulation(mode="mobile", scenario_id="S04", model=stub_model_factory(0.01))
    try:
        simulation.start_scenario()
        simulation.run_until_pause()
        assert simulation.case.status == "DIGITAL_COMPLETED"
        assert simulation.staff_take_over()["ok"] is False
    finally:
        simulation.close()
