"""
Financial Analysis Engine — calculates all key financial ratios.
"""
from ..logger import get_logger

logger = get_logger(__name__)


def calculate_financial_ratios(
    financial_records: list[dict],
    existing_loans: list[dict],
    operational_data: dict | None = None,
) -> dict:
    """
    Calculate comprehensive financial ratios from farmer data.

    Uses the most recent year's financial record as primary input.
    Returns a dict of all calculated ratios with interpretations.
    """
    if not financial_records:
        return {"error": "No financial records available"}

    # Use most recent year
    latest = sorted(financial_records, key=lambda r: r["year"], reverse=True)[0]

    revenue = max(latest.get("revenue", 0), 1)
    net_income = latest.get("net_income", 0)
    total_assets = max(latest.get("total_assets", 0), 1)
    total_liabilities = latest.get("total_liabilities", 0)
    current_assets = latest.get("current_assets", 0)
    current_liabilities = max(latest.get("current_liabilities", 0), 1)
    operating_expenses = latest.get("operating_expenses", 0)
    interest_expense = max(latest.get("interest_expense", 0), 1)
    depreciation = latest.get("depreciation", 0)
    operating_cash_flow = latest.get("operating_cash_flow", 0)
    long_term_debt = latest.get("long_term_debt", 0)
    equity = max(latest.get("equity", 0), 1)

    # Total annual debt service (from existing loans)
    total_annual_emi = sum(loan.get("annual_debt_service", 0) or
                           (loan.get("monthly_emi", 0) * 12)
                           for loan in existing_loans)
    total_outstanding = sum(loan.get("outstanding_balance", 0) for loan in existing_loans)

    # EBITDA
    ebitda = net_income + interest_expense + depreciation

    # --- Core Ratios ---

    # 1. Debt-to-Income Ratio (DTI)
    debt_to_income = (total_annual_emi / revenue) if revenue else 0

    # 2. Debt Service Coverage Ratio (DSCR)
    dscr = (ebitda / total_annual_emi) if total_annual_emi else 999

    # 3. Working Capital
    working_capital = current_assets - current_liabilities

    # 4. Operating Profit Margin
    operating_margin = (net_income / revenue) if revenue else 0

    # 5. Loan-to-Value (using outstanding debt vs total assets)
    loan_to_value = (total_outstanding / total_assets) if total_assets else 0

    # 6. Asset Coverage Ratio
    asset_coverage = (total_assets / total_liabilities) if total_liabilities else 999

    # 7. Current Ratio
    current_ratio = (current_assets / current_liabilities) if current_liabilities else 999

    # 8. Debt-to-Equity
    debt_to_equity = (total_liabilities / equity) if equity else 0

    # 9. Cash Flow Margin
    cash_flow_margin = (operating_cash_flow / revenue) if revenue else 0

    # 10. Interest Coverage Ratio
    interest_coverage = (ebitda / interest_expense) if interest_expense else 999

    # --- Revenue per acre (if operational data available) ---
    revenue_per_acre = None
    if operational_data:
        acres = operational_data.get("farm_size_acres", 0)
        if acres:
            revenue_per_acre = revenue / acres

    ratios = {
        "debt_to_income": round(debt_to_income, 4),
        "dscr": round(dscr, 2),
        "working_capital": round(working_capital, 2),
        "operating_margin": round(operating_margin, 4),
        "loan_to_value": round(loan_to_value, 4),
        "asset_coverage": round(asset_coverage, 2),
        "current_ratio": round(current_ratio, 2),
        "debt_to_equity": round(debt_to_equity, 4),
        "cash_flow_margin": round(cash_flow_margin, 4),
        "interest_coverage": round(interest_coverage, 2),
        "revenue_per_acre": round(revenue_per_acre, 2) if revenue_per_acre else None,
        "total_annual_debt_service": round(total_annual_emi, 2),
        "total_outstanding_debt": round(total_outstanding, 2),
        "ebitda": round(ebitda, 2),
        "year": latest.get("year"),
    }

    # --- Risk Flags ---
    flags = []

    if debt_to_income > 0.50:
        flags.append({"indicator": "debt_to_income", "severity": "high",
                       "message": f"DTI ratio of {debt_to_income:.1%} exceeds 50% threshold"})
    elif debt_to_income > 0.40:
        flags.append({"indicator": "debt_to_income", "severity": "medium",
                       "message": f"DTI ratio of {debt_to_income:.1%} is elevated"})

    if dscr < 1.25:
        flags.append({"indicator": "dscr", "severity": "high",
                       "message": f"DSCR of {dscr:.2f}x is below the 1.25x minimum"})
    elif dscr < 1.50:
        flags.append({"indicator": "dscr", "severity": "medium",
                       "message": f"DSCR of {dscr:.2f}x is below the 1.50x comfort level"})

    if loan_to_value > 0.60:
        flags.append({"indicator": "loan_to_value", "severity": "high",
                       "message": f"LTV of {loan_to_value:.1%} exceeds 60% threshold"})

    if current_ratio < 1.0:
        flags.append({"indicator": "current_ratio", "severity": "high",
                       "message": f"Current ratio of {current_ratio:.2f}x — liquidity concern"})

    ratios["risk_flags"] = flags
    ratios["overall_financial_health"] = (
        "good" if len([f for f in flags if f["severity"] == "high"]) == 0
        else "warning" if len([f for f in flags if f["severity"] == "high"]) <= 1
        else "critical"
    )

    # --- Composite Financial Health Score (0-100) ---
    health_score = _calculate_health_score(
        debt_to_income, dscr, operating_margin, loan_to_value,
        current_ratio, asset_coverage, debt_to_equity, cash_flow_margin,
    )
    ratios["composite_health_score"] = health_score

    # --- Trend indicators (year-over-year) ---
    if len(financial_records) >= 2:
        prev = financial_records[1]  # second most recent
        ratios["trends"] = {
            "revenue": _trend(prev.get("revenue", 0), revenue),
            "net_income": _trend(prev.get("net_income", 0), net_income),
            "debt": _trend_inverse(prev.get("total_liabilities", total_liabilities), total_liabilities),
            "cash_flow": _trend(prev.get("operating_cash_flow", 0), operating_cash_flow),
            "dscr_trend": _trend(
                prev_dscr if (prev_dscr := _calc_dscr_for_year(prev, existing_loans)) else dscr,
                dscr,
            ),
        }
    else:
        ratios["trends"] = {}

    # --- Recommendation Category ---
    ratios["recommendation_category"] = _recommendation_category(health_score, flags, dscr, debt_to_income)

    # --- Provenance summary ---
    ratios["provenance"] = {
        "revenue": latest.get("source_document", "Financial Statement"),
        "debt": existing_loans[0].get("loan_type", "Loan Statement") if existing_loans else "N/A",
        "assets": latest.get("source_document", "Financial Statement"),
    }

    logger.info(f"Financial ratios calculated for year {latest.get('year')}: "
                f"DTI={debt_to_income:.2%}, DSCR={dscr:.2f}x, "
                f"Health={ratios['overall_financial_health']}, Score={health_score}/100")

    return ratios


def _trend(prev_val: float, curr_val: float) -> str:
    """Determine trend direction."""
    if curr_val > prev_val * 1.03:
        return "up"
    elif curr_val < prev_val * 0.97:
        return "down"
    return "flat"


def _trend_inverse(prev_val: float, curr_val: float) -> str:
    """For metrics where lower is better (debt)."""
    if curr_val > prev_val * 1.03:
        return "down"  # debt going up is bad = down
    elif curr_val < prev_val * 0.97:
        return "up"    # debt going down is good = up
    return "flat"


def _calc_dscr_for_year(financial: dict, loans: list) -> float | None:
    """Quick DSCR calculation for a single year."""
    ni = financial.get("net_income", 0)
    interest = financial.get("interest_expense", 0)
    depr = financial.get("depreciation", 0)
    ebitda = ni + interest + depr
    annual_service = sum(l.get("annual_debt_service", 0) or (l.get("monthly_emi", 0) * 12) for l in loans)
    if annual_service == 0:
        return None
    return ebitda / annual_service


def _calculate_health_score(dti, dscr, margin, ltv, current_ratio, asset_cov, debt_eq, cf_margin) -> int:
    """Composite financial health score 0-100."""
    score = 50  # baseline

    # DTI: lower is better (0-50% range)
    if dti <= 0.35: score += 15
    elif dti <= 0.45: score += 8
    elif dti <= 0.55: score += 0
    else: score -= 10

    # DSCR: higher is better
    if dscr >= 2.0: score += 15
    elif dscr >= 1.5: score += 10
    elif dscr >= 1.25: score += 5
    elif dscr >= 1.0: score -= 5
    else: score -= 15

    # Operating margin
    if margin >= 0.35: score += 10
    elif margin >= 0.20: score += 5
    elif margin >= 0.10: score += 0
    else: score -= 5

    # LTV: lower is better
    if ltv <= 0.30: score += 10
    elif ltv <= 0.50: score += 5
    elif ltv <= 0.65: score += 0
    else: score -= 10

    # Current ratio
    if current_ratio >= 2.0: score += 5
    elif current_ratio >= 1.0: score += 2
    else: score -= 5

    return max(0, min(100, score))


def _recommendation_category(score: int, flags: list, dscr: float, dti: float) -> dict:
    """Generate recommendation category with reasoning."""
    high_flags = [f for f in flags if f["severity"] == "high"]

    if score >= 75 and len(high_flags) == 0 and dscr >= 1.5:
        category = "Proceed"
        color = "#2e7d32"
        reasoning = "Strong financial position with comfortable debt service coverage and low leverage."
    elif score >= 55 and len(high_flags) <= 1 and dscr >= 1.25:
        category = "Proceed with Conditions"
        color = "#f57f17"
        reasoning = "Adequate financial health. Conditional approval recommended — consider crop insurance or partial collateral."
    elif score >= 35 and dscr >= 1.0:
        category = "Manual Review"
        color = "#e65100"
        reasoning = "Mixed signals. DSCR near minimum threshold. Requires detailed human review of collateral and repayment history."
    else:
        category = "High Risk"
        color = "#c62828"
        reasoning = "Multiple risk indicators suggest elevated default risk. Recommend declining or requesting significant additional collateral."

    return {
        "category": category,
        "color": color,
        "reasoning": reasoning,
        "score": score,
    }
