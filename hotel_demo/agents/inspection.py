"""Kernel inspeksi kandidat kamar (fungsi murni, tanpa side effect).

Dipakai oleh dua jalur agar hasilnya bisa dibandingkan secara adil:
- mobile: ``MobileInvestigator`` menjalankannya setelah migrasi ke node Operations;
- statis: ``OperationsAgent`` menjalankannya atas permintaan batch.
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence


def evaluate_candidates(
    candidate_snapshots: Sequence[Dict[str, Any]],
    readiness_records: Sequence[Dict[str, Any]],
    constraints: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Nilai tiap kandidat kamar: siap pakai? boleh dipindah otomatis?

    Kamar "routine eligible" (boleh dipindah tanpa manusia) jika:
    bersih, tidak diblokir maintenance, tipe sama, dan tarif <= ``max_rate``.
    Setiap kamar juga diberi ``reason_codes`` yang menjelaskan alasannya.
    """
    readiness_by_room = {record["room_id"]: record for record in readiness_records}
    requested_type = constraints.get("room_type")
    max_rate = int(constraints.get("max_rate", 0))
    results: List[Dict[str, Any]] = []

    for candidate in candidate_snapshots:
        room_id = candidate["room_id"]
        readiness = readiness_by_room.get(room_id)

        # Kondisi fisik kamar (dari data Operations).
        clean = bool(readiness) and readiness.get("cleanliness") == "clean"
        blocked = bool(readiness) and bool(readiness.get("maintenance_blocked"))
        is_ready = clean and not blocked

        # Kecocokan dengan permintaan reservasi.
        type_ok = candidate.get("room_type") == requested_type
        rate_ok = int(candidate.get("nightly_rate", 0)) <= max_rate
        is_routine_eligible = is_ready and type_ok and rate_ok

        reason_codes: List[str] = []
        if not clean:
            reason_codes.append("DIRTY")
        if blocked:
            reason_codes.append("MAINTENANCE_BLOCKED")
        if is_ready and not type_ok:
            reason_codes.append("UPGRADE_REQUIRES_HUMAN")
        if is_ready and type_ok and not rate_ok:
            reason_codes.append("RATE_REQUIRES_HUMAN")
        if is_routine_eligible:
            reason_codes.append("READY_EQUAL_ROOM")

        rate_delta = int(candidate.get("nightly_rate", 0)) - int(
            constraints.get("reservation_rate", max_rate)
        )
        results.append(
            {
                "room_id": room_id,
                "room_type": candidate.get("room_type"),
                "nightly_rate": candidate.get("nightly_rate"),
                "room_version": candidate.get("room_version"),
                "evidence_version": None if readiness is None else readiness.get("evidence_version"),
                "is_ready": is_ready,
                "is_routine_eligible": is_routine_eligible,
                "reason_codes": reason_codes,
                "rate_delta": rate_delta,
            }
        )
    return results
