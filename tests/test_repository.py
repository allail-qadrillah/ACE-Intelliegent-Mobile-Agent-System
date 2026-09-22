"""AC-16: seed, dua database terpisah, tiket idempotent, commit atomik, rollback."""

from __future__ import annotations

from hotel_demo.repository import FrontOfficeRepository, OperationsRepository, load_seed


def _repos():
    seed = load_seed()
    return FrontOfficeRepository(seed), OperationsRepository(seed)


def test_seed_consistent_and_nodes_separated():
    front_office, operations = _repos()
    try:
        reservation = front_office.get_reservation("RES001")["reservation"]
        assert reservation["room_id"] == "R101"
        assert reservation["room_type"] == "standard"
        assert reservation["nightly_rate"] == 500000
        assert reservation["status"] == "checked_in"
        assert reservation["version"] == 1

        room = front_office.get_room("R101")["room"]
        assert room["occupied_by"] == "RES001"

        readiness = {item["room_id"]: item for item in operations.get_readiness(["R101", "R102", "R103", "R201"])["readiness"]}
        assert readiness["R101"]["maintenance_blocked"] is True
        assert readiness["R102"]["cleanliness"] == "dirty"
        assert readiness["R103"]["cleanliness"] == "clean"

        tables_fo = {row[0] for row in front_office.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        tables_ops = {row[0] for row in operations.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "reservations" in tables_fo and "reservations" not in tables_ops
        assert "room_readiness" in tables_ops and "room_readiness" not in tables_fo
    finally:
        front_office.close()
        operations.close()


def test_folio_and_faq():
    front_office, operations = _repos()
    try:
        folio = front_office.get_folio("RES001")
        assert [entry["id"] for entry in folio["entries"]] == ["F01", "F02"]
        assert folio["total"] == 650000
        faq = front_office.get_faq("check_in")
        assert faq["answer"] == "Waktu check-in Hotel Nusantara Demo mulai pukul 14.00."
        assert front_office.get_faq("unknown")["ok"] is False
        assert front_office.get_folio("RES404")["error"]["code"] == "NOT_FOUND"
    finally:
        front_office.close()
        operations.close()


def test_create_ticket_is_idempotent():
    _, operations = _repos()
    try:
        first = operations.create_ticket(
            case_id="CASE-001",
            room_id="R101",
            department="MAINTENANCE",
            description="Perbaikan AC kamar R101",
            operation_key="ticket:CASE-001:maintenance",
        )
        second = operations.create_ticket(
            case_id="CASE-001",
            room_id="R101",
            department="MAINTENANCE",
            description="Perbaikan AC kamar R101",
            operation_key="ticket:CASE-001:maintenance",
        )
        assert first["ticket"]["id"] == second["ticket"]["id"] == "TICKET-001"
        assert second["idempotent"] is True
        assert len(operations.list_tickets()) == 1
    finally:
        operations.close()


def test_ticket_transitions_and_maintenance_release():
    _, operations = _repos()
    try:
        operations.create_ticket(
            case_id="CASE-001",
            room_id="R101",
            department="MAINTENANCE",
            description="Perbaikan AC",
            operation_key="ticket:CASE-001:maintenance",
        )
        assert operations.update_ticket_status("TICKET-001", "DONE")["error"]["code"] == "INVALID_TRANSITION"
        assert operations.update_ticket_status("TICKET-001", "IN_PROGRESS")["ok"] is True
        before = {item["room_id"]: item for item in operations.get_readiness(["R101"])["readiness"]}
        assert before["R101"]["maintenance_blocked"] is True
        assert operations.update_ticket_status("TICKET-001", "DONE")["ok"] is True
        after = {item["room_id"]: item for item in operations.get_readiness(["R101"])["readiness"]}
        assert after["R101"]["maintenance_blocked"] is False
        assert after["R101"]["evidence_version"] == before["R101"]["evidence_version"] + 1
    finally:
        operations.close()


def _valid_commit_kwargs():
    return {
        "reservation_id": "RES001",
        "target_room_id": "R103",
        "case_id": "CASE-001",
        "expected_versions": {"reservation": 1, "original_room": 1, "room": 1, "readiness": 1},
        "fresh_readiness": {
            "room_id": "R103",
            "cleanliness": "clean",
            "maintenance_blocked": False,
            "evidence_version": 1,
        },
        "consent": {
            "case_id": "CASE-001",
            "proposed_room_id": "R103",
            "proposal_version": 1,
            "accepted": True,
            "actor": "GUEST",
        },
        "operation_key": "roomchange:CASE-001:R103",
        "policy_decision": {"human_required": False},
        "case": {"case_id": "CASE-001", "proposal_version": 1},
        "recheck_correlation_id": "RECHECK-CASE-001",
        "expected_recheck_correlation": "RECHECK-CASE-001",
    }


def test_commit_room_change_is_atomic_and_idempotent():
    front_office, _ = _repos()
    try:
        first = front_office.commit_room_change(**_valid_commit_kwargs())
        assert first["ok"] is True
        assert first["result"]["from_room_id"] == "R101"
        assert first["result"]["to_room_id"] == "R103"
        assert front_office.get_reservation("RES001")["reservation"]["room_id"] == "R103"
        assert front_office.get_room("R103")["room"]["occupied_by"] == "RES001"
        assert front_office.get_room("R101")["room"]["occupied_by"] is None
        assert front_office.get_room("R101")["room"]["version"] == 2
        assert front_office.get_room("R103")["room"]["version"] == 2
        assert front_office.get_reservation("RES001")["reservation"]["version"] == 2

        second = front_office.commit_room_change(**_valid_commit_kwargs())
        assert second["ok"] is True
        assert second["idempotent"] is True
        assert front_office.get_room("R103")["room"]["version"] == 2
        assert front_office.get_reservation("RES001")["reservation"]["version"] == 2
    finally:
        front_office.close()


def test_commit_refusal_leaves_no_partial_change():
    front_office, _ = _repos()
    try:
        kwargs = _valid_commit_kwargs()
        kwargs["expected_versions"] = {"reservation": 99, "original_room": 1, "room": 1, "readiness": 1}
        result = front_office.commit_room_change(**kwargs)
        assert result["ok"] is False
        assert result["error"]["code"] == "STALE_ROOM_STATE"
        assert front_office.get_reservation("RES001")["reservation"]["room_id"] == "R101"
        assert front_office.get_room("R101")["room"]["occupied_by"] == "RES001"
        assert front_office.get_room("R103")["room"]["occupied_by"] is None
        assert front_office.get_room("R101")["room"]["version"] == 1
    finally:
        front_office.close()


def test_commit_refuses_when_policy_requires_human():
    front_office, _ = _repos()
    try:
        kwargs = _valid_commit_kwargs()
        kwargs["policy_decision"] = {"human_required": True}
        result = front_office.commit_room_change(**kwargs)
        assert result["ok"] is False
        assert "HUMAN_REQUIRED" in result["error"]["details"]["reason_codes"]
        assert front_office.get_reservation("RES001")["reservation"]["room_id"] == "R101"
    finally:
        front_office.close()


def test_commit_refuses_mismatched_recheck_correlation():
    front_office, _ = _repos()
    try:
        kwargs = _valid_commit_kwargs()
        kwargs["recheck_correlation_id"] = "RECHECK-OTHER"
        result = front_office.commit_room_change(**kwargs)
        assert result["ok"] is False
        assert result["error"]["code"] == "STALE_ROOM_STATE"
    finally:
        front_office.close()
