"""
Data Quality & Preprocessing Engine

Validates, cleans, and flags issues in farmer financial data.
Designed for agricultural lending — never silently modifies data.
All flagged issues are surfaced to the loan officer for review.

Steps:
  1. Data Validation — reject impossible values
  2. Missing Value Detection — identify & suggest strategies
  3. Duplicate Detection — find duplicate records
  4. Outlier Detection — flag (never auto-remove)
  5. Data Standardization — currency, units, dates
  6. Data Ambiguity — conflicting values across documents
"""
import re
from datetime import datetime
from typing import Any

import numpy as np

from ..logger import get_logger

logger = get_logger(__name__)

# ---- Validation Rules ----
VALIDATION_RULES = {
    "revenue": {"min": 0, "max": 50_000_000, "unit": "SEK", "description": "Annual farm revenue"},
    "operating_expenses": {"min": 0, "max": 40_000_000, "unit": "SEK"},
    "net_income": {"min": -10_000_000, "max": 20_000_000, "unit": "SEK"},
    "total_assets": {"min": 100_000, "max": 100_000_000, "unit": "SEK"},
    "total_liabilities": {"min": 0, "max": 80_000_000, "unit": "SEK"},
    "farm_size_acres": {"min": 0.5, "max": 5000, "unit": "hectares", "description": "Farm size"},
    "crop_yield_kg": {"min": 100, "max": 50_000_000, "unit": "kg"},
    "interest_rate": {"min": 0.1, "max": 25.0, "unit": "%", "description": "Annual interest rate"},
    "monthly_emi": {"min": 100, "max": 5_000_000, "unit": "SEK"},
    "cibil_score": {"min": 300, "max": 900, "unit": "UC Score"},
    "years_in_farming": {"min": 1, "max": 60, "unit": "years"},
    "expected_price_per_kg": {"min": 0.50, "max": 50.0, "unit": "SEK/kg"},
    "loan_to_value": {"min": 0, "max": 2.0, "unit": "ratio"},
    "dscr": {"min": 0, "max": 50.0, "unit": "ratio"},
    "debt_to_income": {"min": 0, "max": 5.0, "unit": "ratio"},
    "operating_margin": {"min": -2.0, "max": 2.0, "unit": "ratio"},
    "current_ratio": {"min": 0, "max": 50.0, "unit": "ratio"},
}


# ---- Missing Value Strategies ----
MISSING_VALUE_STRATEGIES = {
    "financial": "median_by_farm_size",      # Revenue, expenses → median of similar farms
    "operational": "most_frequent_by_region", # Crop type → most common in region
    "weather": "api_fallback",               # Rainfall → fetch from API or recent average
    "commodity": "latest_available",         # Prices → most recent known value
    "loan": "zero_or_flag",                  # If no loan exists → 0, flag if loan exists but missing
    "identity": "flag_only",                 # Name, email → flag, cannot impute
}


def validate_farmer_data(farmer_data: dict) -> list[dict]:
    """
    Validate all farmer financial data against defined rules.

    Returns list of validation issues found.
    """
    issues = []

    for field, rules in VALIDATION_RULES.items():
        value = farmer_data.get(field)
        if value is None:
            continue

        try:
            value = float(value)
        except (ValueError, TypeError):
            issues.append({
                "type": "validation_error",
                "field": field,
                "value": str(value),
                "severity": "high",
                "message": f"{field}: '{value}' is not a valid number",
                "action": "Reject — request corrected value",
            })
            continue

        if value < rules["min"]:
            issues.append({
                "type": "validation_error",
                "field": field,
                "value": value,
                "severity": "high",
                "message": f"{field}: {value} is below minimum ({rules['min']} {rules.get('unit','')})",
                "action": "Reject — value is impossible",
            })
        elif value > rules["max"]:
            issues.append({
                "type": "validation_error",
                "field": field,
                "value": value,
                "severity": "high",
                "message": f"{field}: {value} exceeds maximum ({rules['max']} {rules.get('unit','')})",
                "action": "Reject — value is impossible",
            })

    return issues


def detect_missing_values(farmer_data: dict) -> list[dict]:
    """
    Detect missing values and suggest appropriate strategies.

    Returns list of missing value issues with recommended actions.
    """
    issues = []

    # Critical financial fields
    financial_fields = ["revenue", "operating_expenses", "net_income", "total_assets", "total_liabilities"]
    for field in financial_fields:
        if farmer_data.get(field) is None or farmer_data.get(field) == 0:
            issues.append({
                "type": "missing_value",
                "field": field,
                "severity": "high",
                "strategy": MISSING_VALUE_STRATEGIES["financial"],
                "message": f"{field} is missing — will use median of similar-sized farms",
                "action": f"Impute using regional median for farms of similar size",
            })

    # Operational fields
    op_fields = ["crop_type", "farm_size_acres", "land_ownership"]
    for field in op_fields:
        if farmer_data.get(field) is None:
            issues.append({
                "type": "missing_value",
                "field": field,
                "severity": "medium",
                "strategy": MISSING_VALUE_STRATEGIES["operational"],
                "message": f"{field} is missing — will use most common value in region",
                "action": "Impute from regional agricultural statistics",
            })

    # Loan fields
    if farmer_data.get("outstanding_balance") is None and farmer_data.get("monthly_emi") is not None:
        issues.append({
            "type": "missing_value",
            "field": "outstanding_balance",
            "severity": "high",
            "strategy": MISSING_VALUE_STRATEGIES["loan"],
            "message": "Loan EMI exists but outstanding balance is missing",
            "action": "Flag for manual review — cannot estimate debt without balance",
        })

    return issues


def detect_duplicates(records: list[dict], key_fields: list[str] | None = None) -> list[dict]:
    """
    Detect duplicate records based on key fields.

    For financial records: same year + same farmer = duplicate.
    For documents: same filename + same farmer = duplicate.
    """
    if key_fields is None:
        key_fields = ["farmer_id", "year"]

    issues = []
    seen = {}

    for i, record in enumerate(records):
        key = tuple(str(record.get(f, "")) for f in key_fields)
        if key in seen:
            issues.append({
                "type": "duplicate",
                "fields": key_fields,
                "record_index": i,
                "duplicate_of": seen[key],
                "severity": "medium",
                "message": f"Duplicate record detected (indices {seen[key]} and {i})",
                "action": "Keep most recent, flag duplicate for review",
            })
        else:
            seen[key] = i

    return issues


def detect_outliers(values: list[float], field_name: str, method: str = "iqr") -> list[dict]:
    """
    Detect outliers using IQR method. Flags but NEVER removes.

    IQR: values outside [Q1 - 1.5*IQR, Q3 + 1.5*IQR] are outliers.
    """
    if len(values) < 4:
        return []

    arr = np.array(values, dtype=float)
    arr = arr[~np.isnan(arr)]

    if method == "iqr":
        q1 = np.percentile(arr, 25)
        q3 = np.percentile(arr, 75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
    elif method == "zscore":
        mean = np.mean(arr)
        std = np.std(arr)
        if std == 0:
            return []
        lower = mean - 3 * std
        upper = mean + 3 * std
    else:
        return []

    issues = []
    for i, val in enumerate(values):
        if val is not None and (val < lower or val > upper):
            distance = "above" if val > upper else "below"
            threshold = upper if val > upper else lower
            issues.append({
                "type": "outlier",
                "field": field_name,
                "value": val,
                "index": i,
                "severity": "medium",
                "method": method,
                "threshold": round(threshold, 2),
                "distance": distance,
                "message": f"{field_name}: {val:,.0f} is {distance} threshold ({threshold:,.0f})",
                "action": "Flag for review — do NOT automatically remove",
            })

    return issues


def detect_outliers_dataset(dataset: list[dict]) -> list[dict]:
    """Run outlier detection on all numeric fields in a dataset."""
    all_issues = []
    numeric_fields = [
        "revenue", "operating_expenses", "net_income", "total_assets",
        "total_liabilities", "farm_size_acres", "crop_yield_kg",
        "interest_rate", "monthly_emi",
    ]

    for field in numeric_fields:
        values = [d.get(field) for d in dataset if d.get(field) is not None]
        if len(values) >= 4:
            issues = detect_outliers(values, field)
            all_issues.extend(issues)

    return all_issues


def standardize_currency(value: float, from_currency: str, to_currency: str = "SEK") -> dict:
    """
    Standardize currency values. Flags conversion.

    Does NOT auto-convert without documenting it.
    """
    # Approximate rates (for demo — would use real API in production)
    rates = {"SEK": 1.0, "EUR": 11.5, "USD": 10.5, "DKK": 1.55, "NOK": 1.05}

    if from_currency == to_currency:
        return {"original": value, "converted": value, "rate": 1.0, "converted": False}

    rate = rates.get(from_currency)
    if rate is None:
        return {"original": value, "converted": None, "rate": None, "error": f"Unknown currency: {from_currency}"}

    converted = round(value * rate, 2)
    return {
        "original": value,
        "original_currency": from_currency,
        "converted": converted,
        "target_currency": to_currency,
        "rate": rate,
        "converted": True,
        "warning": f"⚠️ Converted from {from_currency} to {to_currency} at rate {rate}. Verify before use.",
    }


def standardize_area(value: float, from_unit: str, to_unit: str = "hectares") -> dict:
    """Standardize area units."""
    conversions = {"hectares": 1.0, "acres": 0.404686, "ha": 1.0, "sqm": 0.0001}

    if from_unit == to_unit:
        return {"original": value, "converted": value, "converted": False}

    factor = conversions.get(from_unit)
    if factor is None:
        return {"original": value, "converted": None, "error": f"Unknown unit: {from_unit}"}

    # Convert to hectares
    in_hectares = value * factor
    return {
        "original": value,
        "original_unit": from_unit,
        "converted": round(in_hectares, 2),
        "target_unit": to_unit,
        "converted": True,
        "warning": f"Converted from {from_unit} to hectares. Original: {value} {from_unit}.",
    }


def detect_ambiguity(source_a: dict, source_b: dict, field: str,
                     source_a_name: str = "Document A",
                     source_b_name: str = "Document B",
                     tolerance_pct: float = 10.0) -> dict | None:
    """
    Detect conflicting values for the same field across two documents.

    Returns conflict details if values differ beyond tolerance.
    """
    val_a = source_a.get(field)
    val_b = source_b.get(field)

    if val_a is None or val_b is None:
        return None
    if val_a == val_b:
        return None

    try:
        va = float(val_a)
        vb = float(val_b)
    except (ValueError, TypeError):
        return None

    if va == 0 and vb == 0:
        return None

    diff_pct = abs(va - vb) / max(abs(va), abs(vb), 1) * 100

    if diff_pct > tolerance_pct:
        return {
            "type": "ambiguity",
            "field": field,
            f"{source_a_name}": va,
            f"{source_b_name}": vb,
            "difference_pct": round(diff_pct, 1),
            "severity": "high" if diff_pct > 25 else "medium",
            "message": (f"Conflicting {field}: {source_a_name}={va:,.0f} vs "
                       f"{source_b_name}={vb:,.0f} ({diff_pct:.0f}% difference)"),
            "action": "Flag for manual review — do NOT auto-resolve",
        }

    return None


def run_full_preprocessing(farmer_id: int, financial_records: list[dict],
                           loans: list[dict], operational: dict | None) -> dict:
    """
    Run the complete preprocessing pipeline and return a quality report.

    This is the main entry point called before ML training or prediction.
    """
    report = {
        "farmer_id": farmer_id,
        "timestamp": datetime.now().isoformat(),
        "summary": {},
        "validation": [],
        "missing_values": [],
        "duplicates": [],
        "outliers": [],
        "ambiguities": [],
        "actions_taken": [],
        "fields_requiring_review": [],
    }

    # 1. Validation — check all financial records
    for record in financial_records:
        issues = validate_farmer_data(record)
        report["validation"].extend(issues)

    # 2. Missing values
    for record in financial_records:
        issues = detect_missing_values(record)
        report["missing_values"].extend(issues)

    # 3. Duplicates
    dup_issues = detect_duplicates(financial_records)
    report["duplicates"] = dup_issues

    # 4. Outliers (across all farmers)
    outlier_issues = detect_outliers_dataset(financial_records)
    report["outliers"] = outlier_issues

    # 5. Ambiguity — compare latest two financial records
    if len(financial_records) >= 2:
        for field in ["revenue", "operating_expenses", "total_assets"]:
            ambiguity = detect_ambiguity(
                financial_records[0], financial_records[1], field,
                "Latest Year", "Previous Year",
            )
            if ambiguity:
                report["ambiguities"].append(ambiguity)

    # 6. Summary
    high_severity = sum(
        1 for i in report["validation"] + report["missing_values"] + report["outliers"]
        if i.get("severity") == "high"
    )
    medium_severity = sum(
        1 for i in report["validation"] + report["missing_values"] + report["outliers"]
        if i.get("severity") == "medium"
    )

    report["summary"] = {
        "total_records": len(financial_records),
        "validation_errors": len(report["validation"]),
        "missing_values": len(report["missing_values"]),
        "duplicates": len(report["duplicates"]),
        "outliers": len(report["outliers"]),
        "ambiguities": len(report["ambiguities"]),
        "high_severity_issues": high_severity,
        "medium_severity_issues": medium_severity,
        "data_quality_score": _calculate_quality_score(
            len(financial_records),
            len(report["validation"]),
            len(report["missing_values"]),
            len(report["duplicates"]),
            len(report["outliers"]),
        ),
    }

    logger.info(f"Preprocessing complete for farmer {farmer_id}: "
                f"quality_score={report['summary']['data_quality_score']}/100, "
                f"issues={high_severity + medium_severity}")

    return report


def _calculate_quality_score(n_records: int, n_validation: int, n_missing: int,
                             n_duplicates: int, n_outliers: int) -> int:
    """Calculate data quality score (0-100)."""
    if n_records == 0:
        return 0
    # Base score from issues per record
    issues_per_record = (n_validation * 3 + n_missing * 2 + n_duplicates * 2 + n_outliers) / n_records
    score = max(0, 100 - int(issues_per_record * 15))
    return min(100, score)
