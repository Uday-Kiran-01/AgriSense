"""
Decision Readiness Engine

Evaluates whether enough trustworthy evidence exists to make a lending decision.
Separates "how risky is the applicant" from "how reliable is the evidence."

Answers:
  - Are all required documents present? (Completeness)
  - Are they recent enough? (Freshness)
  - Are there conflicts between sources? (Ambiguity)
  - Is enough evidence available? (Decision Readiness)

Three outcomes:
  1. Ready for assessment
  2. Assessment possible, but confidence reduced
  3. Insufficient evidence — manual review required
"""
from datetime import datetime, date
from typing import Any

from ..logger import get_logger

logger = get_logger(__name__)

# ---- Required documents for a complete application ----
REQUIRED_DOCUMENTS = {
    "financial_statement": {
        "label": "Financial Statement (Balans/Resultaträkning)",
        "required": True,
        "max_age_months": 18,
        "weight": 25,  # contribution to completeness score
    },
    "bank_statement": {
        "label": "Bank Statement (Bankutdrag)",
        "required": True,
        "max_age_months": 6,
        "weight": 20,
    },
    "loan_doc": {
        "label": "Loan Documents (Låneavtal)",
        "required": True,
        "max_age_months": None,  # no expiry — historical loans are valid
        "weight": 15,
    },
    "land_record": {
        "label": "Land Records (Lagfart/Fastighetsbevis)",
        "required": True,
        "max_age_months": None,  # land ownership doesn't expire
        "weight": 15,
    },
    "farm_doc": {
        "label": "Production Reports (Skörderapport)",
        "required": False,  # strongly recommended but not mandatory
        "max_age_months": 12,
        "weight": 10,
    },
    "insurance": {
        "label": "Insurance Policy (Försäkringsbrev)",
        "required": False,
        "max_age_months": 12,
        "weight": 10,
    },
    "tax_return": {
        "label": "Tax Return (Deklaration)",
        "required": False,
        "max_age_months": 18,
        "weight": 5,
    },
}

# ---- Data freshness thresholds ----
FRESHNESS_THRESHOLDS = {
    "financial_records": {"max_age_months": 18, "label": "Financial Records", "weight": 30},
    "bank_statements": {"max_age_months": 6, "label": "Bank Statements", "weight": 25},
    "operational_data": {"max_age_months": 12, "label": "Farm Operations Data", "weight": 20},
    "weather_data": {"max_age_days": 7, "label": "Weather Data", "weight": 15},
    "commodity_data": {"max_age_days": 30, "label": "Commodity Prices", "weight": 10},
}

# ---- Minimum requirements for automated assessment ----
MIN_COMPLETENESS_FOR_AUTO = 70  # %
MIN_FRESHNESS_FOR_AUTO = 60    # %


def assess_document_completeness(documents: list[dict]) -> dict:
    """
    Check which required documents are present vs missing.

    Returns completeness score and breakdown.
    """
    present_types = {d.get("document_type", "") for d in documents}

    total_weight = 0
    earned_weight = 0
    breakdown = []

    for doc_type, config in REQUIRED_DOCUMENTS.items():
        is_present = doc_type in present_types
        weight = config["weight"]

        if is_present:
            earned_weight += weight

        total_weight += weight if config["required"] else weight

        breakdown.append({
            "document_type": doc_type,
            "label": config["label"],
            "required": config["required"],
            "present": is_present,
            "weight": weight,
        })

    completeness_pct = round((earned_weight / total_weight * 100) if total_weight > 0 else 0, 1)
    missing_required = [b for b in breakdown if b["required"] and not b["present"]]
    missing_recommended = [b for b in breakdown if not b["required"] and not b["present"]]

    return {
        "completeness_pct": completeness_pct,
        "documents_present": sum(1 for b in breakdown if b["present"]),
        "documents_total": len(breakdown),
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
        "breakdown": breakdown,
        "status": _completeness_status(completeness_pct, missing_required),
    }


def _completeness_status(pct: float, missing_required: list) -> str:
    if pct >= 90 and len(missing_required) == 0:
        return "Complete — all required documents present"
    elif pct >= 70:
        return f"Incomplete — {len(missing_required)} required document(s) missing"
    else:
        return "Insufficient — missing critical documents"


def assess_data_freshness(financial_records: list[dict],
                          operational_data: dict | None = None) -> dict:
    """
    Check how recent the available data is.
    Older data = lower confidence.

    Returns freshness score and per-category assessment.
    """
    now = date.today()
    total_weight = sum(f["weight"] for f in FRESHNESS_THRESHOLDS.values())
    earned_weight = 0
    breakdown = []

    # Financial records freshness
    if financial_records:
        latest_year = max(r.get("year", 0) for r in financial_records)
        years_old = now.year - latest_year
        months_old = years_old * 12
        max_age = FRESHNESS_THRESHOLDS["financial_records"]["max_age_months"]

        if months_old <= max_age:
            freshness = 100
        elif months_old <= max_age * 2:
            freshness = 70
        elif months_old <= max_age * 3:
            freshness = 40
        else:
            freshness = 15

        weight = FRESHNESS_THRESHOLDS["financial_records"]["weight"]
        earned_weight += weight * freshness / 100

        breakdown.append({
            "category": "financial_records",
            "label": "Financial Records",
            "latest_year": latest_year,
            "age_months": months_old,
            "max_age_months": max_age,
            "freshness_pct": freshness,
            "weight": weight,
            "warning": f"Financial data is {years_old} year(s) old. Confidence reduced." if years_old >= 2 else None,
        })

    # Operational data freshness
    if operational_data:
        # Operational data from seed has created_at — use that if available
        created = operational_data.get("created_at")
        if isinstance(created, datetime):
            age_days = (now - created.date()).days
        else:
            age_days = 180  # assume moderate age if unknown

        max_days = FRESHNESS_THRESHOLDS["operational_data"]["max_age_months"] * 30
        freshness = max(10, 100 - (age_days / max_days * 100))
        weight = FRESHNESS_THRESHOLDS["operational_data"]["weight"]
        earned_weight += weight * freshness / 100

        breakdown.append({
            "category": "operational_data",
            "label": "Farm Operations Data",
            "age_days": age_days,
            "freshness_pct": round(freshness, 1),
            "weight": weight,
        })

    # Weather data (mock is always "current")
    breakdown.append({
        "category": "weather_data",
        "label": "Weather Data",
        "age_days": 1,
        "freshness_pct": 95,
        "weight": FRESHNESS_THRESHOLDS["weather_data"]["weight"],
        "note": "Mock data — real API would provide current readings",
    })
    earned_weight += FRESHNESS_THRESHOLDS["weather_data"]["weight"] * 0.95

    # Commodity data
    breakdown.append({
        "category": "commodity_data",
        "label": "Commodity Prices",
        "age_days": 3,
        "freshness_pct": 90,
        "weight": FRESHNESS_THRESHOLDS["commodity_data"]["weight"],
        "note": "Mock data — real API would provide current prices",
    })
    earned_weight += FRESHNESS_THRESHOLDS["commodity_data"]["weight"] * 0.90

    freshness_pct = round((earned_weight / total_weight * 100) if total_weight > 0 else 0, 1)

    return {
        "freshness_pct": min(100, freshness_pct),
        "breakdown": breakdown,
        "status": _freshness_status(freshness_pct),
    }


def _freshness_status(pct: float) -> str:
    if pct >= 80:
        return "Current — all data is within acceptable ranges"
    elif pct >= 60:
        return "Aging — some data may be outdated"
    else:
        return "Stale — significant data is outdated. Confidence heavily reduced."


def assess_evidence_quality(
    completeness_pct: float,
    freshness_pct: float,
    n_conflicts: int = 0,
    n_outliers: int = 0,
    n_validation_errors: int = 0,
) -> dict:
    """
    Composite evidence quality score.

    Weights:
    - Completeness: 35%
    - Freshness: 35%
    - Conflicts (-): 15%
    - Outliers (-): 10%
    - Validation errors (-): 5%
    """
    conflict_penalty = min(15, n_conflicts * 5)
    outlier_penalty = min(10, n_outliers * 2)
    validation_penalty = min(5, n_validation_errors * 1)

    quality = (
        completeness_pct * 0.35 +
        freshness_pct * 0.35 +
        (100 - conflict_penalty) * 0.15 +
        (100 - outlier_penalty) * 0.10 +
        (100 - validation_penalty) * 0.05
    )

    quality = round(min(100, max(0, quality)), 1)

    if quality >= 85:
        status = "Strong — sufficient, recent, and consistent evidence"
    elif quality >= 65:
        status = "Adequate — some gaps or aging data, but assessment possible"
    elif quality >= 45:
        status = "Weak — significant evidence gaps. Confidence reduced."
    else:
        status = "Insufficient — manual review required before assessment"

    return {
        "evidence_quality_pct": quality,
        "status": status,
        "components": {
            "completeness": round(completeness_pct, 1),
            "freshness": round(freshness_pct, 1),
            "conflict_penalty": conflict_penalty,
            "outlier_penalty": outlier_penalty,
            "validation_penalty": validation_penalty,
        },
    }


def calculate_decision_readiness(
    evidence_quality_pct: float,
    model_confidence: float | None = None,
    n_manual_review_flags: int = 0,
) -> dict:
    """
    Final decision readiness — can the AI make a recommendation?

    Three outcomes:
      1. Ready for assessment
      2. Assessment possible, but confidence reduced
      3. Insufficient evidence — manual review required
    """
    # Model confidence reduces readiness if low
    model_factor = (model_confidence or 0.85) * 100

    readiness = (
        evidence_quality_pct * 0.60 +
        model_factor * 0.30 +
        max(0, 100 - n_manual_review_flags * 20) * 0.10
    )

    readiness = round(min(100, max(0, readiness)), 1)

    if readiness >= 75 and n_manual_review_flags == 0:
        level = "ready"
        message = "Ready for automated assessment. All critical evidence is present and current."
        recommendation = "Proceed with AI-assisted evaluation."
    elif readiness >= 50:
        level = "reduced_confidence"
        message = (f"Assessment possible but confidence is reduced. "
                   f"Evidence quality: {evidence_quality_pct:.0f}%. "
                   f"{n_manual_review_flags} item(s) flagged for review.")
        recommendation = "AI assessment available with caveats. Human review recommended for flagged items."
    else:
        level = "insufficient"
        message = (f"Insufficient reliable evidence for automated assessment. "
                   f"Evidence quality: {evidence_quality_pct:.0f}%. "
                   f"Additional documentation or manual review required.")
        recommendation = "Human review required. Do not rely solely on AI assessment."

    return {
        "decision_readiness_pct": readiness,
        "level": level,
        "message": message,
        "recommendation": recommendation,
        "components": {
            "evidence_quality": evidence_quality_pct,
            "model_confidence": round(model_factor, 1) if model_confidence else None,
            "manual_review_flags": n_manual_review_flags,
        },
    }


def run_full_readiness_assessment(
    farmer_id: int,
    documents: list[dict],
    financial_records: list[dict],
    operational_data: dict | None,
    n_conflicts: int = 0,
    n_outliers: int = 0,
    n_validation_errors: int = 0,
    model_confidence: float | None = None,
) -> dict:
    """
    Complete decision readiness assessment.
    Assembles all scores into one report.
    """
    completeness = assess_document_completeness(documents)
    freshness = assess_data_freshness(financial_records, operational_data)
    evidence = assess_evidence_quality(
        completeness["completeness_pct"],
        freshness["freshness_pct"],
        n_conflicts, n_outliers, n_validation_errors,
    )
    readiness = calculate_decision_readiness(
        evidence["evidence_quality_pct"],
        model_confidence,
        len(completeness.get("missing_required", [])),
    )

    report = {
        "farmer_id": farmer_id,
        "timestamp": datetime.now().isoformat(),
        "completeness": completeness,
        "freshness": freshness,
        "evidence_quality": evidence,
        "decision_readiness": readiness,
        "summary": {
            "completeness": f"{completeness['completeness_pct']:.0f}%",
            "freshness": f"{freshness['freshness_pct']:.0f}%",
            "evidence_quality": f"{evidence['evidence_quality_pct']:.0f}%",
            "decision_readiness": f"{readiness['decision_readiness_pct']:.0f}%",
            "level": readiness["level"],
            "can_assess": readiness["level"] != "insufficient",
            "needs_human_review": readiness["level"] in ("reduced_confidence", "insufficient"),
        },
    }

    logger.info(f"Decision readiness for farmer {farmer_id}: "
                f"{readiness['decision_readiness_pct']:.0f}% ({readiness['level']})")

    return report
