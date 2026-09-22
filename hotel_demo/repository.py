"""Dua database SQLite in-memory terpisah (Front Office dan Operations).

Berisi seed, guarded tools, transaksi perubahan kamar atomik, tiket idempotent,
serta dump/close. Engine tetap single-thread/sequential.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from . import policy

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SEED_PATH = DATA_DIR / "hotel_seed.json"


def ok(**kwargs: Any) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"ok": True}
    payload.update(kwargs)
    return payload


def err(code: str, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "ok": False,
        "error": {"code": code, "message": message, "details": details or {}},
    }


def load_seed(path: Optional[Path] = None) -> Dict[str, Any]:
    seed_path = Path(path) if path else SEED_PATH
    with open(seed_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _merge_by_id(
    base: Iterable[Dict[str, Any]],
    overrides: Iterable[Dict[str, Any]],
    key: str = "id",
) -> List[Dict[str, Any]]:
    merged: Dict[Any, Dict[str, Any]] = {}
    order: List[Any] = []
    for item in base:
        merged[item[key]] = dict(item)
        order.append(item[key])
    for item in overrides or []:
        if item[key] in merged:
            merged[item[key]].update(item)
        else:
            merged[item[key]] = dict(item)
            order.append(item[key])
    return [merged[k] for k in order]


class FrontOfficeRepository:
    """Database lokal node FRONT_OFFICE (reservasi, kamar, folio, FAQ, kasus)."""

    def __init__(
        self, seed: Optional[Dict[str, Any]] = None, overrides: Optional[Dict[str, Any]] = None
    ) -> None:
        self.conn = sqlite3.connect(":memory:", check_same_thread=False, isolation_level=None)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_schema()
        self._seed(seed or load_seed(), overrides or {})

    # ------------------------------------------------------------------ schema
    def _create_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE guests (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL
            );
            CREATE TABLE rooms (
                id TEXT PRIMARY KEY,
                room_type TEXT NOT NULL,
                nightly_rate INTEGER NOT NULL,
                occupied_by TEXT NULL REFERENCES reservations(id),
                version INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE reservations (
                id TEXT PRIMARY KEY,
                guest_id TEXT NOT NULL REFERENCES guests(id),
                room_id TEXT NOT NULL REFERENCES rooms(id),
                room_type TEXT NOT NULL,
                nightly_rate INTEGER NOT NULL,
                status TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE folio_entries (
                id TEXT PRIMARY KEY,
                reservation_id TEXT NOT NULL REFERENCES reservations(id),
                description TEXT NOT NULL,
                amount INTEGER NOT NULL
            );
            CREATE TABLE faq (
                key TEXT PRIMARY KEY,
                answer TEXT NOT NULL
            );
            CREATE TABLE cases (
                id TEXT PRIMARY KEY,
                scenario_id TEXT NOT NULL,
                status TEXT NOT NULL,
                human_required INTEGER NOT NULL DEFAULT 0,
                reason_codes_json TEXT NOT NULL DEFAULT '[]',
                proposed_room_id TEXT NULL,
                proposal_version INTEGER NOT NULL DEFAULT 0,
                consent_json TEXT NULL,
                priority TEXT NOT NULL DEFAULT 'NORMAL',
                state_json TEXT NULL
            );
            CREATE TABLE audit_events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            CREATE TABLE applied_operations (
                operation_key TEXT PRIMARY KEY,
                result_json TEXT NOT NULL
            );
            """
        )

    def _seed(self, seed: Dict[str, Any], overrides: Dict[str, Any]) -> None:
        guests = _merge_by_id(seed.get("guests", []), overrides.get("guests", []))
        rooms = _merge_by_id(seed.get("rooms", []), overrides.get("rooms", []))
        reservations = _merge_by_id(
            seed.get("reservations", []), overrides.get("reservations", [])
        )
        folio = _merge_by_id(
            seed.get("folio_entries", []), overrides.get("folio_entries", [])
        )
        faq = _merge_by_id(seed.get("faq", []), overrides.get("faq", []), key="key")

        for guest in guests:
            self.conn.execute(
                "INSERT INTO guests (id, name) VALUES (?, ?)", (guest["id"], guest["name"])
            )
        for room in rooms:
            self.conn.execute(
                "INSERT INTO rooms (id, room_type, nightly_rate, occupied_by, version)"
                " VALUES (?, ?, ?, NULL, ?)",
                (
                    room["id"],
                    room["room_type"],
                    int(room["nightly_rate"]),
                    int(room.get("version", 1)),
                ),
            )
        for res in reservations:
            self.conn.execute(
                "INSERT INTO reservations"
                " (id, guest_id, room_id, room_type, nightly_rate, status, version)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    res["id"],
                    res["guest_id"],
                    res["room_id"],
                    res["room_type"],
                    int(res["nightly_rate"]),
                    res["status"],
                    int(res.get("version", 1)),
                ),
            )
        for room in rooms:
            occupied_by = room.get("occupied_by")
            if occupied_by:
                self.conn.execute(
                    "UPDATE rooms SET occupied_by = ? WHERE id = ?", (occupied_by, room["id"])
                )
        for entry in folio:
            self.conn.execute(
                "INSERT INTO folio_entries (id, reservation_id, description, amount)"
                " VALUES (?, ?, ?, ?)",
                (
                    entry["id"],
                    entry["reservation_id"],
                    entry["description"],
                    int(entry["amount"]),
                ),
            )
        for item in faq:
            self.conn.execute(
                "INSERT INTO faq (key, answer) VALUES (?, ?)",
                (item["key"], item["answer"]),
            )

    # -------------------------------------------------------------- operasi DB
    def close(self) -> None:
        self.conn.close()

    # -------------------------------------------------------------- tools read
    def get_reservation(self, reservation_id: str) -> Dict[str, Any]:
        row = self.conn.execute(
            "SELECT * FROM reservations WHERE id = ?", (reservation_id,)
        ).fetchone()
        if row is None:
            return err(
                "NOT_FOUND",
                f"Reservasi {reservation_id} tidak ditemukan.",
                {"reservation_id": reservation_id},
            )
        return ok(reservation=dict(row))

    def get_room(self, room_id: str) -> Dict[str, Any]:
        row = self.conn.execute("SELECT * FROM rooms WHERE id = ?", (room_id,)).fetchone()
        if row is None:
            return err("NOT_FOUND", f"Kamar {room_id} tidak ditemukan.", {"room_id": room_id})
        return ok(room=dict(row))

    def find_candidates(
        self, reservation_id: str, include_upgrade_alternatives: bool = False
    ) -> Dict[str, Any]:
        reservation = self.get_reservation(reservation_id)
        if not reservation["ok"]:
            return reservation
        res = reservation["reservation"]
        rows = self.conn.execute(
            "SELECT * FROM rooms WHERE occupied_by IS NULL ORDER BY id"
        ).fetchall()
        candidates = []
        for row in rows:
            room = dict(row)
            if not include_upgrade_alternatives and room["room_type"] != res["room_type"]:
                continue
            candidates.append(
                {
                    "room_id": room["id"],
                    "room_type": room["room_type"],
                    "nightly_rate": room["nightly_rate"],
                    "room_version": room["version"],
                }
            )
        return ok(candidates=candidates, reservation=res)

    def get_folio(self, reservation_id: str) -> Dict[str, Any]:
        reservation = self.get_reservation(reservation_id)
        if not reservation["ok"]:
            return reservation
        rows = self.conn.execute(
            "SELECT * FROM folio_entries WHERE reservation_id = ? ORDER BY id",
            (reservation_id,),
        ).fetchall()
        entries = [dict(row) for row in rows]
        total = sum(int(entry["amount"]) for entry in entries)
        return ok(entries=entries, total=total)

    def get_faq(self, key: str) -> Dict[str, Any]:
        row = self.conn.execute("SELECT * FROM faq WHERE key = ?", (key,)).fetchone()
        if row is None:
            return err("FAQ_UNKNOWN", f"FAQ '{key}' tidak tersedia.", {"key": key})
        return ok(key=row["key"], answer=row["answer"])

    # ----------------------------------------------------------- cases & audit
    def sync_case(self, case: Dict[str, Any]) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO cases"
            " (id, scenario_id, status, human_required, reason_codes_json,"
            "  proposed_room_id, proposal_version, consent_json, priority, state_json)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                case["case_id"],
                case["scenario_id"],
                case["status"],
                1 if case["human_required"] else 0,
                json.dumps(case["human_reason_codes"], ensure_ascii=False),
                case["proposed_room_id"],
                int(case["proposal_version"]),
                None if case["consent"] is None else json.dumps(case["consent"], ensure_ascii=False),
                case["priority"],
                json.dumps(case, ensure_ascii=False),
            ),
        )

    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        row = self.conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
        return None if row is None else dict(row)

    def append_audit(self, event_type: str, payload: Dict[str, Any]) -> None:
        self.conn.execute(
            "INSERT INTO audit_events (event_type, payload_json) VALUES (?, ?)",
            (event_type, json.dumps(payload, ensure_ascii=False, sort_keys=True)),
        )

    def audit_events(self) -> List[Dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM audit_events ORDER BY seq").fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------ idempotency
    def get_applied(self, operation_key: str) -> Optional[Dict[str, Any]]:
        row = self.conn.execute(
            "SELECT result_json FROM applied_operations WHERE operation_key = ?",
            (operation_key,),
        ).fetchone()
        return None if row is None else json.loads(row["result_json"])

    def _save_applied(self, operation_key: str, result: Dict[str, Any]) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO applied_operations (operation_key, result_json) VALUES (?, ?)",
            (operation_key, json.dumps(result, ensure_ascii=False, sort_keys=True)),
        )

    # --------------------------------------------------------- commit kamar
    def commit_room_change(
        self,
        *,
        reservation_id: str,
        target_room_id: str,
        case_id: str,
        expected_versions: Dict[str, Any],
        fresh_readiness: Optional[Dict[str, Any]],
        consent: Optional[Dict[str, Any]],
        operation_key: str,
        policy_decision: Optional[Dict[str, Any]],
        case: Optional[Dict[str, Any]],
        recheck_correlation_id: Optional[str],
        expected_recheck_correlation: Optional[str],
    ) -> Dict[str, Any]:
        applied = self.get_applied(operation_key)
        if applied is not None:
            return ok(result=applied, idempotent=True)

        reservation_res = self.get_reservation(reservation_id)
        if not reservation_res["ok"]:
            return reservation_res
        reservation = reservation_res["reservation"]

        target_res = self.get_room(target_room_id)
        target_room = target_res.get("room") if target_res["ok"] else None
        original_res = self.get_room(reservation["room_id"])
        original_room = original_res.get("room") if original_res["ok"] else None

        codes = policy.validate_room_change(
            policy_decision=policy_decision,
            consent=consent,
            case=case,
            reservation=reservation,
            target_room=target_room,
            original_room=original_room,
            fresh_readiness=fresh_readiness,
            expected_versions=expected_versions,
            recheck_correlation_id=recheck_correlation_id,
            expected_recheck_correlation=expected_recheck_correlation,
        )
        if codes:
            return err(
                policy.summarize_commit_refusal(codes),
                "Perubahan kamar ditolak karena validasi ulang tidak terpenuhi.",
                {"reason_codes": codes, "operation_key": operation_key},
            )

        assert target_room is not None and original_room is not None
        result = {
            "reservation_id": reservation_id,
            "case_id": case_id,
            "from_room_id": original_room["id"],
            "to_room_id": target_room["id"],
            "operation_key": operation_key,
            "versions": {
                "reservation": reservation["version"] + 1,
                "original_room": original_room["version"] + 1,
                "room": target_room["version"] + 1,
            },
        }
        try:
            self.conn.execute("BEGIN")
            self.conn.execute(
                "UPDATE rooms SET occupied_by = NULL, version = version + 1 WHERE id = ?",
                (original_room["id"],),
            )
            self.conn.execute(
                "UPDATE rooms SET occupied_by = ?, version = version + 1 WHERE id = ?",
                (reservation_id, target_room["id"]),
            )
            self.conn.execute(
                "UPDATE reservations SET room_id = ?, version = version + 1 WHERE id = ?",
                (target_room["id"], reservation_id),
            )
            self._save_applied(operation_key, result)
            self.conn.execute("COMMIT")
        except Exception as exc:  # pragma: no cover - jalur kegagalan teknis
            self.conn.execute("ROLLBACK")
            return err(
                "TRANSACTION_FAILED",
                "Transaksi perubahan kamar gagal dan di-rollback.",
                {"exception": str(exc)},
            )
        return ok(result=result)

    # ------------------------------------------------------------------ dump
    def dump(self) -> Dict[str, Any]:
        tables = [
            "guests",
            "rooms",
            "reservations",
            "folio_entries",
            "faq",
            "cases",
            "audit_events",
            "applied_operations",
        ]
        snapshot: Dict[str, Any] = {}
        for table in tables:
            rows = self.conn.execute(f"SELECT * FROM {table}").fetchall()
            snapshot[table] = [dict(row) for row in rows]
        return snapshot


class OperationsRepository:
    """Database lokal node OPERATIONS (readiness, tiket)."""

    def __init__(
        self, seed: Optional[Dict[str, Any]] = None, overrides: Optional[Dict[str, Any]] = None
    ) -> None:
        self.conn = sqlite3.connect(":memory:", check_same_thread=False, isolation_level=None)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._ticket_counter = 0
        self._create_schema()
        self._seed(seed or load_seed(), overrides or {})

    def _create_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE room_readiness (
                room_id TEXT PRIMARY KEY,
                cleanliness TEXT NOT NULL,
                maintenance_blocked INTEGER NOT NULL DEFAULT 0,
                evidence_version INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE tickets (
                id TEXT PRIMARY KEY,
                operation_key TEXT NOT NULL UNIQUE,
                case_id TEXT NOT NULL,
                room_id TEXT NOT NULL,
                department TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL
            );
            CREATE TABLE applied_operations (
                operation_key TEXT PRIMARY KEY,
                result_json TEXT NOT NULL
            );
            """
        )

    def _seed(self, seed: Dict[str, Any], overrides: Dict[str, Any]) -> None:
        readiness = _merge_by_id(
            seed.get("room_readiness", []), overrides.get("room_readiness", []), key="room_id"
        )
        for item in readiness:
            self.conn.execute(
                "INSERT INTO room_readiness"
                " (room_id, cleanliness, maintenance_blocked, evidence_version)"
                " VALUES (?, ?, ?, ?)",
                (
                    item["room_id"],
                    item["cleanliness"],
                    1 if item["maintenance_blocked"] else 0,
                    int(item.get("evidence_version", 1)),
                ),
            )

    def close(self) -> None:
        self.conn.close()

    # ---------------------------------------------------------------- tools
    def get_readiness(self, room_ids: Iterable[str]) -> Dict[str, Any]:
        snapshots = []
        for room_id in room_ids:
            row = self.conn.execute(
                "SELECT * FROM room_readiness WHERE room_id = ?", (room_id,)
            ).fetchone()
            if row is None:
                continue
            snapshots.append(
                {
                    "room_id": row["room_id"],
                    "cleanliness": row["cleanliness"],
                    "maintenance_blocked": bool(row["maintenance_blocked"]),
                    "evidence_version": row["evidence_version"],
                }
            )
        return ok(readiness=snapshots)

    def set_maintenance_block(self, room_id: str, blocked: bool) -> None:
        self.conn.execute(
            "UPDATE room_readiness SET maintenance_blocked = ?,"
            " evidence_version = evidence_version + 1 WHERE room_id = ?",
            (1 if blocked else 0, room_id),
        )

    def get_applied(self, operation_key: str) -> Optional[Dict[str, Any]]:
        row = self.conn.execute(
            "SELECT result_json FROM applied_operations WHERE operation_key = ?",
            (operation_key,),
        ).fetchone()
        return None if row is None else json.loads(row["result_json"])

    def _save_applied(self, operation_key: str, result: Dict[str, Any]) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO applied_operations (operation_key, result_json) VALUES (?, ?)",
            (operation_key, json.dumps(result, ensure_ascii=False, sort_keys=True)),
        )

    def create_ticket(
        self,
        *,
        case_id: str,
        room_id: str,
        department: str,
        description: str,
        operation_key: str,
    ) -> Dict[str, Any]:
        applied = self.get_applied(operation_key)
        if applied is not None:
            return ok(ticket=applied, idempotent=True)
        self._ticket_counter += 1
        ticket_id = f"TICKET-{self._ticket_counter:03d}"
        self.conn.execute(
            "INSERT INTO tickets"
            " (id, operation_key, case_id, room_id, department, description, status)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (ticket_id, operation_key, case_id, room_id, department, description, "PENDING"),
        )
        ticket = {
            "id": ticket_id,
            "operation_key": operation_key,
            "case_id": case_id,
            "room_id": room_id,
            "department": department,
            "description": description,
            "status": "PENDING",
        }
        self._save_applied(operation_key, ticket)
        return ok(ticket=ticket)

    def update_ticket_status(
        self, ticket_id: str, next_status: str, actor: str = "STAFF"
    ) -> Dict[str, Any]:
        row = self.conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if row is None:
            return err("NOT_FOUND", f"Tiket {ticket_id} tidak ditemukan.", {"ticket_id": ticket_id})
        ticket = dict(row)
        allowed = {"PENDING": ["IN_PROGRESS"], "IN_PROGRESS": ["DONE"], "DONE": []}
        if next_status not in allowed.get(ticket["status"], []):
            return err(
                "INVALID_TRANSITION",
                f"Transisi tiket {ticket['status']} -> {next_status} tidak diizinkan.",
                {"ticket_id": ticket_id, "from": ticket["status"], "to": next_status},
            )
        self.conn.execute(
            "UPDATE tickets SET status = ? WHERE id = ?", (next_status, ticket_id)
        )
        ticket["status"] = next_status
        if next_status == "DONE" and ticket["department"] == "MAINTENANCE":
            self.set_maintenance_block(ticket["room_id"], False)
        return ok(ticket=ticket, actor=actor)

    def list_tickets(self) -> List[Dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM tickets ORDER BY id").fetchall()
        return [dict(row) for row in rows]

    def dump(self) -> Dict[str, Any]:
        snapshot: Dict[str, Any] = {}
        for table in ("room_readiness", "tickets", "applied_operations"):
            rows = self.conn.execute(f"SELECT * FROM {table}").fetchall()
            snapshot[table] = [dict(row) for row in rows]
        return snapshot
