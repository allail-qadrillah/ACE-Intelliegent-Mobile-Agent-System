"""Policy wajib, prediksi ML, dan validasi perubahan kamar.

Policy adalah lapisan aturan yang tidak dapat dilangkahi agen. Mandatory flags
selalu menang atas probabilitas ML rendah.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import PolicyDecision

DEFAULT_THRESHOLD = 0.80

MANDATORY_FLAGS = (
    "emergency",
    "request_human",
    "financial_dispute",
    "compensation_requested",
    "upgrade_exception",
)

FLAG_REASON = {
    "emergency": "EMERGENCY",
    "request_human": "GUEST_REQUESTED_HUMAN",
    "financial_dispute": "FINANCIAL_DISPUTE",
    "compensation_requested": "COMPENSATION_REQUESTED",
    "upgrade_exception": "UPGRADE_REQUIRES_HUMAN",
}

ML_REASON = "ML_HIGH_HUMAN_PROBABILITY"

# Reason code yang menandakan snapshot kamar sudah usang / tidak layak commit.
STALE_CODES = {
    "STALE_ROOM_STATE",
    "ROOM_OCCUPIED",
    "ROOM_NOT_FOUND",
    "NOT_READY",
    "MAINTENANCE_BLOCKED",
    "SAME_ROOM",
    "TYPE_MISMATCH",
    "RATE_HIGHER",
    "NOT_CHECKED_IN",
}


def evaluate_case(
    flags: Optional[Dict[str, Any]],
    probability: float,
    threshold: float = DEFAULT_THRESHOLD,
) -> PolicyDecision:
    """Prioritas keputusan: mandatory flags > ML >= threshold > rutin."""
    flags = flags or {}
    mandatory = [flag for flag in MANDATORY_FLAGS if flags.get(flag)]
    model_recommends = float(probability) >= float(threshold)

    if mandatory:
        return PolicyDecision(
            human_required=True,
            decision_source="POLICY",
            reason_codes=[FLAG_REASON[flag] for flag in mandatory],
            priority="URGENT" if flags.get("emergency") else "NORMAL",
            p_human=float(probability),
            threshold=float(threshold),
            model_recommends_human=model_recommends,
            mandatory_reasons=[FLAG_REASON[flag] for flag in mandatory],
        )

    if model_recommends:
        return PolicyDecision(
            human_required=True,
            decision_source="ML",
            reason_codes=[ML_REASON],
            priority="NORMAL",
            p_human=float(probability),
            threshold=float(threshold),
            model_recommends_human=True,
            mandatory_reasons=[],
        )

    return PolicyDecision(
        human_required=False,
        decision_source="POLICY_AND_ML",
        reason_codes=[],
        priority="NORMAL",
        p_human=float(probability),
        threshold=float(threshold),
        model_recommends_human=False,
        mandatory_reasons=[],
    )


def validate_room_change(
    *,
    policy_decision: Optional[Dict[str, Any]],
    consent: Optional[Dict[str, Any]],
    case: Optional[Dict[str, Any]],
    reservation: Optional[Dict[str, Any]],
    target_room: Optional[Dict[str, Any]],
    original_room: Optional[Dict[str, Any]],
    fresh_readiness: Optional[Dict[str, Any]],
    expected_versions: Optional[Dict[str, Any]],
    recheck_correlation_id: Optional[str],
    expected_recheck_correlation: Optional[str],
) -> List[str]:
    """Validasi murni (tanpa DB). Mengembalikan daftar reason code.

    Repository tetap memanggil ini sebelum menulis, dan runtime/tool tetap
    memvalidasi agar direct call tidak melewati aturan.
    """
    codes: List[str] = []
    policy_decision = policy_decision or {}
    consent = consent or {}
    case = case or {}
    reservation = reservation or {}
    target_room = target_room or {}
    original_room = original_room or {}
    fresh_readiness = fresh_readiness or {}
    expected_versions = expected_versions or {}

    if policy_decision.get("human_required"):
        codes.append("HUMAN_REQUIRED")

    if not consent.get("accepted"):
        codes.append("CONSENT_MISSING")
    else:
        if consent.get("case_id") != case.get("case_id"):
            codes.append("CONSENT_MISMATCH")
        if consent.get("proposed_room_id") != target_room.get("id"):
            codes.append("CONSENT_MISMATCH")
        if consent.get("proposal_version") != case.get("proposal_version"):
            codes.append("CONSENT_MISMATCH")

    if (
        not recheck_correlation_id
        or recheck_correlation_id != expected_recheck_correlation
    ):
        codes.append("STALE_ROOM_STATE")

    if reservation.get("status") != "checked_in":
        codes.append("NOT_CHECKED_IN")
    if reservation.get("version") != expected_versions.get("reservation"):
        codes.append("STALE_ROOM_STATE")
    if not original_room or original_room.get("version") != expected_versions.get(
        "original_room"
    ):
        codes.append("STALE_ROOM_STATE")

    if not target_room:
        codes.append("ROOM_NOT_FOUND")
    else:
        if target_room.get("id") == reservation.get("room_id"):
            codes.append("SAME_ROOM")
        if target_room.get("occupied_by") is not None:
            codes.append("ROOM_OCCUPIED")
        if target_room.get("version") != expected_versions.get("room"):
            codes.append("STALE_ROOM_STATE")
        if target_room.get("room_type") != reservation.get("room_type"):
            codes.append("TYPE_MISMATCH")
        if int(target_room.get("nightly_rate", 0)) > int(
            reservation.get("nightly_rate", 0)
        ):
            codes.append("RATE_HIGHER")

    if fresh_readiness.get("cleanliness") != "clean":
        codes.append("NOT_READY")
    if fresh_readiness.get("maintenance_blocked"):
        codes.append("MAINTENANCE_BLOCKED")
    if fresh_readiness.get("evidence_version") != expected_versions.get("readiness"):
        codes.append("STALE_ROOM_STATE")

    return codes


def summarize_commit_refusal(codes: List[str]) -> str:
    """Reason code tingkat kasus untuk penolakan commit."""
    for code in codes:
        if code in STALE_CODES:
            return "STALE_ROOM_STATE"
    return codes[0] if codes else "COMMIT_REFUSED"
