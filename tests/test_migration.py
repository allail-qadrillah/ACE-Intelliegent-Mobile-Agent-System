"""AC-02 s/d AC-06, AC-17, AC-30: migrasi state, invariant ownership, kegagalan."""

from __future__ import annotations

import json

from hotel_demo import migration as migration_module
from hotel_demo.models import canonical_json, sha256_hex

FORBIDDEN_FIELDS = ("repository", "model", "connection", "sqlite", "ui", "functions", "pipeline")


def _step_until(simulation, predicate, limit: int = 80):
    for _ in range(limit):
        if predicate(simulation):
            return
        simulation.step()
    raise AssertionError("Predicate tidak tercapai dalam batas langkah.")


def _to_stage(simulation, stage: str):
    _step_until(
        simulation,
        lambda sim: sim.migration is not None and sim.migration.stage == stage,
    )
    return simulation.migration


def _to_arrived(simulation):
    _step_until(
        simulation,
        lambda sim: sim.last_migration is not None
        and sim.last_migration.stage == "SUCCEEDED",
    )
    return simulation.last_migration


def test_prepare_creates_valid_checkpoint(make_sim):
    simulation = make_sim("S01")
    simulation.start_scenario()
    record = _to_stage(simulation, "PREPARED")

    assert record.original_bytes
    parsed = json.loads(record.original_bytes.decode("utf-8"))
    assert parsed["agent_id"] == "MA-001"
    assert parsed["case_id"] == "CASE-001"
    assert parsed["goal"] == "FIND_READY_REPLACEMENT_ROOM"
    assert parsed["phase"] == "INSPECT_LOCAL"
    assert parsed["schema_version"] == 1
    assert parsed["code_version"] == "investigator-v1"
    assert [candidate["room_id"] for candidate in parsed["candidate_rooms"]] == ["R102", "R103"]
    assert parsed["visited_nodes"] == ["FRONT_OFFICE"]
    assert parsed["migration_count"] == 0

    for field in FORBIDDEN_FIELDS:
        assert field not in parsed

    assert record.expected_hash == sha256_hex(record.original_bytes)
    assert record.checkpoint_size == len(record.original_bytes)
    assert simulation.owner_by_agent["MA-001"] == "FRONT_OFFICE"
    assert simulation.agents["MA-001"].status == "SUSPENDED"
    assert simulation.active_instance_count("MA-001") == 1
    assert any(event.event_type == "MIGRATION_PREPARED" for event in simulation.events)


def test_depart_removes_active_owner(make_sim):
    simulation = make_sim("S01")
    simulation.start_scenario()
    record = _to_stage(simulation, "DEPARTED")

    assert simulation.active_instance_count("MA-001") == 0
    assert simulation.owner_by_agent["MA-001"] is None
    assert record.in_transit_bytes is not None
    assert simulation.agents["MA-001"].status == "IN_TRANSIT"
    assert simulation.metrics["transferred_checkpoint_bytes"] == record.checkpoint_size
    assert any(event.event_type == "MIGRATION_DEPARTED" for event in simulation.events)


def test_arrive_recreates_instance_with_continuity(make_sim):
    simulation = make_sim("S01")
    simulation.start_scenario()
    source = None
    _step_until(simulation, lambda sim: "MA-001" in sim.agents)
    source = simulation.agents["MA-001"]

    _to_arrived(simulation)
    destination = simulation.agents["MA-001"]

    assert destination is not source
    assert destination.agent_id == "MA-001"
    assert destination.case_id == "CASE-001"
    assert destination.node_id == "OPERATIONS"
    assert destination.current_node == "OPERATIONS"
    assert destination.phase == "INSPECT_LOCAL"
    assert destination.migration_count == 1
    assert destination.visited_nodes == ["FRONT_OFFICE", "OPERATIONS"]
    assert [candidate["room_id"] for candidate in destination.candidate_rooms] == ["R102", "R103"]
    assert simulation.owner_by_agent["MA-001"] == "OPERATIONS"
    assert simulation.active_instance_count("MA-001") == 1
    assert simulation.metrics["migrations_succeeded"] == 1


def test_checkpoint_serialization_breaks_shared_references(make_sim):
    simulation = make_sim("S01")
    simulation.start_scenario()
    _step_until(simulation, lambda sim: "MA-001" in sim.agents)
    source = simulation.agents["MA-001"]

    _to_arrived(simulation)
    record = simulation.last_migration
    destination = simulation.agents["MA-001"]

    source.candidate_rooms.append({"room_id": "HACK"})
    source.constraints["room_type"] = "hacked"
    record.before_snapshot["candidate_rooms"].append({"room_id": "HACK-2"})

    assert [candidate["room_id"] for candidate in destination.candidate_rooms] == ["R102", "R103"]
    assert destination.constraints["room_type"] == "standard"


def test_local_read_denied_at_front_office_and_allowed_after_arrival(make_sim):
    simulation = make_sim("S01")
    simulation.start_scenario()
    _step_until(
        simulation,
        lambda sim: "MA-001" in sim.agents and sim.migration is None,
    )
    assert simulation.agents["MA-001"].node_id == "FRONT_OFFICE"

    denied = simulation.read_local_readiness("MA-001", ["R103"])
    assert denied["ok"] is False
    assert denied["error"]["code"] in ("WRONG_NODE", "NOT_OWNER")

    _to_arrived(simulation)
    allowed = simulation.read_local_readiness("MA-001", ["R103"])
    assert allowed["ok"] is True
    assert allowed["readiness"][0]["room_id"] == "R103"


def test_migration_invariants_hold_every_step(make_sim):
    simulation = make_sim("S01")
    simulation.start_scenario()
    for _ in range(80):
        for agent_id in list(simulation.agents):
            assert simulation.active_instance_count(agent_id) <= 1
            owner = simulation.owner_by_agent.get(agent_id)
            if owner is not None:
                holders = [
                    node_id
                    for node_id, node in simulation.nodes.items()
                    if agent_id in node.active_agents
                ]
                assert holders == [owner], f"{agent_id} owner={owner} holders={holders}"
        if simulation.migration is not None and simulation.migration.stage == "DEPARTED":
            assert simulation.active_instance_count("MA-001") == 0
            assert simulation.owner_by_agent["MA-001"] is None
            assert simulation.migration.in_transit_bytes
        if not simulation.has_pending_work():
            break
        simulation.step()
    assert simulation.case.status == "WAITING_GUEST"


def test_arrive_replay_is_noop(make_sim):
    simulation = make_sim("S01")
    simulation.start_scenario()
    _to_arrived(simulation)
    record = simulation.last_migration
    before = len(simulation.events)

    migration_module.arrive(simulation, record)

    assert simulation.metrics["migrations_succeeded"] == 1
    assert simulation.active_instance_count("MA-001") == 1
    assert any(
        event.event_type == "DUPLICATE_IGNORED" for event in simulation.events[before:]
    )


def test_arrive_rejects_corrupted_hash(make_sim):
    simulation = make_sim("S01")
    simulation.start_scenario()
    record = _to_stage(simulation, "DEPARTED")
    payload = record.in_transit_bytes
    record.in_transit_bytes = payload[:-1] + bytes([payload[-1] ^ 0xFF])

    simulation.step()

    assert simulation.last_migration.stage == "FAILED"
    assert simulation.last_migration.error["code"] == "HASH_MISMATCH"
    assert simulation.metrics["migrations_failed"] == 1
    assert simulation.case.status == "WAITING_HUMAN"
    assert "MIGRATION_FAILED" in simulation.case.human_reason_codes
    assert simulation.owner_by_agent["MA-001"] == "FRONT_OFFICE"
    assert simulation.active_instance_count("MA-001") == 1


def test_arrive_rejects_unsupported_schema(make_sim):
    simulation = make_sim("S01")
    simulation.start_scenario()
    record = _to_stage(simulation, "DEPARTED")
    parsed = json.loads(record.in_transit_bytes.decode("utf-8"))
    parsed["schema_version"] = 99
    data = canonical_json(parsed)
    record.in_transit_bytes = data
    record.expected_hash = sha256_hex(data)

    simulation.step()

    assert simulation.last_migration.error["code"] == "SCHEMA_UNSUPPORTED"
    assert simulation.case.status == "WAITING_HUMAN"


def test_arrive_rejects_unsupported_code_version(make_sim):
    simulation = make_sim("S01")
    simulation.start_scenario()
    record = _to_stage(simulation, "DEPARTED")
    parsed = json.loads(record.in_transit_bytes.decode("utf-8"))
    parsed["code_version"] = "investigator-v99"
    data = canonical_json(parsed)
    record.in_transit_bytes = data
    record.expected_hash = sha256_hex(data)

    simulation.step()

    assert simulation.last_migration.error["code"] == "CODE_VERSION_UNSUPPORTED"


def test_prepare_rejects_inactive_destination(make_sim):
    simulation = make_sim("S01")
    simulation.start_scenario()
    _step_until(simulation, lambda sim: sim.migration is not None)
    assert simulation.migration.stage == "INITIATED"
    simulation.nodes["OPERATIONS"].active = False

    simulation.step()

    assert simulation.last_migration is not None
    assert simulation.last_migration.error["code"] == "DESTINATION_INACTIVE"
    assert simulation.case.status == "WAITING_HUMAN"
    assert simulation.owner_by_agent["MA-001"] == "FRONT_OFFICE"
    assert simulation.active_instance_count("MA-001") == 1
    assert simulation.agents["MA-001"].status == "ACTIVE"
    assert simulation.metrics["migrations_failed"] == 1


def test_arrive_rejects_inactive_destination_and_restores_source(make_sim):
    simulation = make_sim("S01")
    simulation.start_scenario()
    _to_stage(simulation, "DEPARTED")
    simulation.nodes["OPERATIONS"].active = False

    simulation.step()

    assert simulation.last_migration.error["code"] == "DESTINATION_INACTIVE"
    assert simulation.case.status == "WAITING_HUMAN"
    assert simulation.owner_by_agent["MA-001"] == "FRONT_OFFICE"
    assert simulation.active_instance_count("MA-001") == 1
    assert simulation.agents["MA-001"].status == "FAILED"


def test_tampered_node_field_is_rejected(make_sim):
    simulation = make_sim("S01")
    simulation.start_scenario()
    record = _to_stage(simulation, "DEPARTED")
    parsed = json.loads(record.in_transit_bytes.decode("utf-8"))
    parsed["current_node"] = "OPERATIONS"
    data = canonical_json(parsed)
    record.in_transit_bytes = data
    record.expected_hash = sha256_hex(data)

    simulation.step()

    assert simulation.last_migration.error["code"] == "CHECKPOINT_NODE_MISMATCH"


def test_forbidden_runtime_field_in_checkpoint_is_rejected(make_sim):
    simulation = make_sim("S01")
    simulation.start_scenario()
    record = _to_stage(simulation, "DEPARTED")
    parsed = json.loads(record.in_transit_bytes.decode("utf-8"))
    parsed["capabilities"] = ["admin", "inspect_readiness"]
    data = canonical_json(parsed)
    record.in_transit_bytes = data
    record.expected_hash = sha256_hex(data)

    simulation.step()

    assert simulation.last_migration.error["code"] == "CHECKPOINT_FORBIDDEN_FIELDS"
    # Capability tetap berasal dari konfigurasi runtime, bukan checkpoint.
    assert simulation.agents["MA-001"].capabilities == ("inspect_readiness",)
