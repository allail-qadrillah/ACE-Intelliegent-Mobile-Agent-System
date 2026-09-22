"""Simulasi migrasi state mobile agent: PREPARE → DEPART → ARRIVE.

Checkpoint adalah JSON murni (tanpa objek Python, koneksi SQLite, model, atau
credential). Kode agen sudah tersedia di runtime tujuan.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from .models import (
    AgentPhase,
    AgentRuntimeStatus,
    EventType,
    MigrationRecord,
    MigrationStage,
    NodeId,
    canonical_json,
    sha256_hex,
)

SUPPORTED_SCHEMA_VERSIONS = {1}
SUPPORTED_CODE_VERSIONS = {"investigator-v1"}

FORBIDDEN_CHECKPOINT_FIELDS = {
    "repository",
    "repositories",
    "model",
    "ml_model",
    "connection",
    "sqlite",
    "ui",
    "functions",
    "pipeline",
    "credentials",
}

REQUIRED_CHECKPOINT_FIELDS = {
    "schema_version",
    "code_version",
    "agent_id",
    "case_id",
    "goal",
    "phase",
    "current_node",
    "candidate_rooms",
    "visited_nodes",
    "inspection_results",
    "migration_count",
}


class MigrationError(Exception):
    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {"code": self.code, "message": self.message, "details": self.details}


def validate_checkpoint_bytes(
    data: Optional[bytes], record: MigrationRecord, *, check_hash: bool = True
) -> Dict[str, Any]:
    """Validasi terhadap bytes (bukan objek sebelum serialisasi)."""
    if not data:
        raise MigrationError("CHECKPOINT_MISSING", "Checkpoint tidak tersedia.")
    if check_hash and record.expected_hash:
        actual = sha256_hex(data)
        if actual != record.expected_hash:
            raise MigrationError(
                "HASH_MISMATCH",
                "Integritas checkpoint tidak cocok (SHA-256).",
                {"expected": record.expected_hash, "actual": actual},
            )
    try:
        parsed = json.loads(data.decode("utf-8"))
    except Exception as exc:
        raise MigrationError(
            "CHECKPOINT_CORRUPT", "Checkpoint tidak dapat di-deserialisasi.", {"exception": str(exc)}
        )
    if not isinstance(parsed, dict):
        raise MigrationError("CHECKPOINT_CORRUPT", "Checkpoint bukan objek JSON.")

    forbidden = FORBIDDEN_CHECKPOINT_FIELDS.intersection(parsed.keys())
    if forbidden:
        raise MigrationError(
            "CHECKPOINT_FORBIDDEN_FIELDS",
            "Checkpoint memuat field runtime yang tidak diizinkan.",
            {"fields": sorted(forbidden)},
        )
    if parsed.get("schema_version") not in SUPPORTED_SCHEMA_VERSIONS:
        raise MigrationError(
            "SCHEMA_UNSUPPORTED",
            "Schema checkpoint tidak didukung.",
            {"schema_version": parsed.get("schema_version")},
        )
    if parsed.get("code_version") not in SUPPORTED_CODE_VERSIONS:
        raise MigrationError(
            "CODE_VERSION_UNSUPPORTED",
            "Code version checkpoint tidak didukung.",
            {"code_version": parsed.get("code_version")},
        )
    missing = REQUIRED_CHECKPOINT_FIELDS.difference(parsed.keys())
    if missing:
        raise MigrationError(
            "CHECKPOINT_INCOMPLETE",
            "Checkpoint kehilangan field wajib.",
            {"missing": sorted(missing)},
        )
    return parsed


def prepare(sim: Any, record: MigrationRecord) -> None:
    """Tahap M1 — serialisasi, hash, dan validasi parse."""
    agent = sim.agents.get(record.agent_id)
    if agent is None:
        raise MigrationError("SOURCE_MISSING", "Agen sumber tidak ditemukan.")
    if sim.owner_by_agent.get(record.agent_id) != record.source_node:
        raise MigrationError(
            "NOT_OWNER",
            "Node sumber bukan pemilik agen saat ini.",
            {"owner": sim.owner_by_agent.get(record.agent_id)},
        )
    if record.destination_node not in {node.value for node in NodeId}:
        raise MigrationError(
            "DESTINATION_UNKNOWN", "Node tujuan tidak dikenal.", {"destination": record.destination_node}
        )
    if not sim.node_is_active(record.destination_node):
        raise MigrationError(
            "DESTINATION_INACTIVE",
            "Node tujuan tidak aktif.",
            {"destination": record.destination_node},
        )
    if "inspect_readiness" not in agent.capabilities:
        raise MigrationError(
            "MISSING_CAPABILITY",
            "Agen tidak memiliki capability inspect_readiness.",
            {"capabilities": list(agent.capabilities)},
        )

    checkpoint = agent.to_checkpoint()
    payload = canonical_json(checkpoint)
    validate_checkpoint_bytes(payload, record, check_hash=False)

    record.original_bytes = payload
    record.expected_hash = sha256_hex(payload)
    record.checkpoint_size = len(payload)
    record.before_snapshot = agent.state_snapshot()
    agent.status = AgentRuntimeStatus.SUSPENDED.value
    record.stage = MigrationStage.PREPARED.value

    sim.emit(
        EventType.MIGRATION_PREPARED.value,
        agent_id=record.agent_id,
        node_id=record.source_node,
        migration_id=record.migration_id,
        source_node=record.source_node,
        destination_node=record.destination_node,
        details={
            "checkpoint_size": record.checkpoint_size,
            "sha256": record.expected_hash,
            "schema_version": checkpoint["schema_version"],
            "code_version": checkpoint["code_version"],
            "phase": checkpoint["phase"],
        },
    )


def depart(sim: Any, record: MigrationRecord) -> None:
    """Tahap M2 — source inactive, owner None, checkpoint in transit."""
    if record.stage != MigrationStage.PREPARED.value:
        raise MigrationError(
            "INVALID_STAGE", "DEPART hanya boleh dari stage PREPARED.", {"stage": record.stage}
        )
    if not record.original_bytes:
        raise MigrationError("CHECKPOINT_MISSING", "Checkpoint asli tidak tersedia.")

    record.in_transit_bytes = record.original_bytes
    record.transferred_bytes = len(record.original_bytes)

    agent = sim.agents.get(record.agent_id)
    if agent is not None:
        record.source_instance_id = id(agent)
        agent.status = AgentRuntimeStatus.IN_TRANSIT.value

    sim.nodes[record.source_node].active_agents.pop(record.agent_id, None)
    sim.owner_by_agent[record.agent_id] = None
    record.stage = MigrationStage.DEPARTED.value

    sim.metrics["transferred_checkpoint_bytes"] += record.transferred_bytes
    sim.emit(
        EventType.MIGRATION_DEPARTED.value,
        agent_id=record.agent_id,
        node_id=record.source_node,
        migration_id=record.migration_id,
        source_node=record.source_node,
        destination_node=record.destination_node,
        details={
            "transferred_bytes": record.transferred_bytes,
            "owner": None,
            "active_instances": sim.active_instance_count(record.agent_id),
        },
    )


def arrive(sim: Any, record: MigrationRecord) -> None:
    """Tahap M3 — verifikasi ulang, rekonstruksi, registrasi, resume."""
    from .agents import MobileInvestigator

    if record.stage == MigrationStage.SUCCEEDED.value:
        sim.emit(
            EventType.DUPLICATE_IGNORED.value,
            agent_id=record.agent_id,
            migration_id=record.migration_id,
            details={"reason": "MIGRATION_ALREADY_SUCCEEDED"},
        )
        return
    if record.stage != MigrationStage.DEPARTED.value:
        raise MigrationError(
            "INVALID_STAGE", "ARRIVE hanya boleh dari stage DEPARTED.", {"stage": record.stage}
        )
    if not sim.node_is_active(record.destination_node):
        raise MigrationError(
            "DESTINATION_INACTIVE",
            "Node tujuan tidak aktif.",
            {"destination": record.destination_node},
        )

    parsed = validate_checkpoint_bytes(record.in_transit_bytes, record, check_hash=True)

    if parsed.get("agent_id") != record.agent_id or parsed.get("case_id") != record.case_id:
        raise MigrationError(
            "CHECKPOINT_IDENTITY_MISMATCH",
            "Identitas checkpoint tidak cocok dengan MigrationRecord.",
            {"agent_id": parsed.get("agent_id"), "case_id": parsed.get("case_id")},
        )
    if parsed.get("current_node") != record.source_node:
        raise MigrationError(
            "CHECKPOINT_NODE_MISMATCH",
            "current_node checkpoint tidak cocok dengan sumber tepercaya.",
            {"current_node": parsed.get("current_node"), "source_node": record.source_node},
        )

    new_agent = MobileInvestigator.from_checkpoint(parsed)
    new_agent.node_id = record.destination_node
    new_agent.current_node = record.destination_node
    new_agent.visited_nodes = list(parsed.get("visited_nodes", [])) + [record.destination_node]
    new_agent.migration_count = int(parsed.get("migration_count", 0)) + 1
    new_agent.status = AgentRuntimeStatus.ACTIVE.value

    sim.agents[record.agent_id] = new_agent
    sim.nodes[record.destination_node].active_agents[record.agent_id] = new_agent
    sim.owner_by_agent[record.agent_id] = record.destination_node
    record.after_snapshot = new_agent.state_snapshot()
    record.stage = MigrationStage.SUCCEEDED.value

    sim.last_migration = record
    sim.migration = None
    sim.metrics["migrations_succeeded"] += 1
    sim.emit(
        EventType.MIGRATION_ARRIVED.value,
        agent_id=record.agent_id,
        node_id=record.destination_node,
        migration_id=record.migration_id,
        source_node=record.source_node,
        destination_node=record.destination_node,
        details={
            "migration_count": new_agent.migration_count,
            "phase": new_agent.phase,
            "instance_recreated": True,
        },
    )

    sim.enqueue(
        sim.make_message(
            sender=record.agent_id,
            receiver=record.agent_id,
            action="INSPECT_CANDIDATES",
            payload={"resume": True, "migration_id": record.migration_id},
            correlation_id=f"TASK-INSPECT-{record.case_id}",
        )
    )


def restore_source(sim: Any, record: MigrationRecord) -> bool:
    """Kembalikan agen sumber dari salinan checkpoint asli (bukan bytes rusak)."""
    from .agents import MobileInvestigator

    if not record.original_bytes:
        return False
    try:
        parsed = json.loads(record.original_bytes.decode("utf-8"))
        agent = MobileInvestigator.from_checkpoint(parsed)
    except Exception:
        return False
    agent.node_id = record.source_node
    agent.current_node = record.source_node
    agent.status = AgentRuntimeStatus.ACTIVE.value
    agent.phase = AgentPhase.READY_TO_MOVE.value
    sim.agents[record.agent_id] = agent
    sim.nodes[record.source_node].active_agents[record.agent_id] = agent
    sim.owner_by_agent[record.agent_id] = record.source_node
    return True


def begin(sim: Any, agent_id: str, destination_node: str) -> MigrationRecord:
    """Buat MigrationRecord dan suspend source. Tahap PREPARE dijalankan step()."""
    source_node = sim.owner_by_agent.get(agent_id)
    if source_node is None:
        raise MigrationError("NOT_OWNER", "Agen tidak memiliki owner node.")
    record = MigrationRecord(
        migration_id=f"MIG-{sim.migration_counter:03d}",
        agent_id=agent_id,
        case_id=sim.case.case_id if sim.case else "CASE-001",
        source_node=source_node,
        destination_node=destination_node,
    )
    sim.migration_counter += 1
    sim.migration = record
    agent = sim.agents.get(agent_id)
    if agent is not None:
        agent.status = AgentRuntimeStatus.SUSPENDED.value
    return record
