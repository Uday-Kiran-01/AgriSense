"""
Seasonal Cash Flow & Liquidity Stress Test

Agriculture is fundamentally seasonal. Annual DSCR doesn't tell the whole story.
This module evaluates whether a farmer can meet monthly obligations
when revenue arrives in 1-2 harvest peaks, not evenly throughout the year.
"""
import numpy as np
from datetime import datetime

from ..logger import get_logger

logger = get_logger(__name__)

# Monthly cash flow profiles by crop type (Swedish context)
# Values are % of annual revenue arriving each month
SEASONAL_PROFILES = {
    "wheat": {  # Winter wheat: harvest Aug-Sep
        1: 0.01, 2: 0.01, 3: 0.02, 4: 0.03, 5: 0.04, 6: 0.05,
        7: 0.06, 8: 0.28, 9: 0.30, 10: 0.12, 11: 0.05, 12: 0.03,
    },
    "barley": {  # Spring barley: harvest Aug
        1: 0.01, 2: 0.01, 3: 0.02, 4: 0.03, 5: 0.04, 6: 0.04,
        7: 0.05, 8: 0.35, 9: 0.25, 10: 0.10, 11: 0.06, 12: 0.04,
    },
    "mixed_grain": {  # Mixed wheat + barley
        1: 0.01, 2: 0.01, 3: 0.02, 4: 0.03, 5: 0.04, 6: 0.05,
        7: 0.06, 8: 0.30, 9: 0.28, 10: 0.11, 11: 0.05, 12: 0.04,
    },
    "rapeseed": {  # Winter rapeseed: harvest Jul-Aug
        1: 0.01, 2: 0.01, 3: 0.02, 4: 0.03, 5: 0.04, 6: 0.05,
        7: 0.32, 8: 0.28, 9: 0.10, 10: 0.07, 11: 0.04, 12: 0.03,
    },
    "oats": {  # Oats: harvest Aug-Sep
        1: 0.01, 2: 0.01, 3: 0.02, 4: 0.03, 5: 0.04, 6: 0.05,
        7: 0.05, 8: 0.30, 9: 0.28, 10: 0.12, 11: 0.05, 12: 0.04,
    },
    "dairy": {  # Dairy: more even, slight summer peak
        1: 0.07, 2: 0.07, 3: 0.08, 4: 0.08, 5: 0.09, 6: 0.10,
        7: 0.10, 8: 0.09, 9: 0.08, 10: 0.08, 11: 0.08, 12: 0.08,
    },
}

# Monthly cost profiles (inputs, labor, maintenance)
# % of annual operating expenses per month
COST_PROFILES = {
    "grain": {  # Grain farms: high input costs in spring
        1: 0.04, 2: 0.04, 3: 0.13, 4: 0.18, 5: 0.15, 6: 0.08,
        7: 0.06, 8: 0.12, 9: 0.10, 10: 0.05, 11: 0.03, 12: 0.02,
    },
    "dairy": {  # Dairy: steady costs
        1: 0.08, 2: 0.08, 3: 0.09, 4: 0.09, 5: 0.08, 6: 0.08,
        7: 0.08, 8: 0.08, 9: 0.09, 10: 0.09, 11: 0.08, 12: 0.08,
    },
}

MONTH_NAMES = [
    "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def _detect_crop_profile(crop_type: str) -> str:
    """Map crop name to seasonal profile key."""
    crop_lower = crop_type.lower() if crop_type else "mixed_grain"
    if "wheat" in crop_lower or "vete" in crop_lower:
        return "wheat"
    if "barley" in crop_lower or "korn" in crop_lower:
        return "barley"
    if "raps" in crop_lower or "rapeseed" in crop_lower:
        return "rapeseed"
    if "oats" in crop_lower or "havre" in crop_lower:
        return "oats"
    if "dairy" in crop_lower or "milk" in crop_lower:
        return "dairy"
    return "mixed_grain"


def _detect_cost_profile(crop_type: str) -> str:
    crop_lower = crop_type.lower() if crop_type else "grain"
    if "dairy" in crop_lower:
        return "dairy"
    return "grain"


def run_liquidity_stress_test(
    annual_revenue: float,
    annual_opex: float,
    crop_type: str,
    monthly_loan_payments: float,
    existing_cash_reserves: float = 0,
    eu_cap_payment: float = 0,
) -> dict:
    """
    Simulate monthly cash flows and identify liquidity stress.

    Returns month-by-month breakdown with stress indicators.
    """
    crop_key = _detect_crop_profile(crop_type)
    cost_key = _detect_cost_profile(crop_type)

    revenue_profile = SEASONAL_PROFILES.get(crop_key, SEASONAL_PROFILES["mixed_grain"])
    cost_profile = COST_PROFILES.get(cost_key, COST_PROFILES["grain"])

    # CAP payments typically arrive in December (EU)
    cap_month = 12

    months = []
    cumulative_cash = existing_cash_reserves
    lowest_balance = existing_cash_reserves
    stress_months = []
    total_negative_months = 0

    for m in range(1, 13):
        # Revenue inflow
        revenue_in = annual_revenue * revenue_profile.get(m, 0.05)
        if m == cap_month:
            revenue_in += eu_cap_payment

        # Operating costs
        costs_out = annual_opex * cost_profile.get(m, 0.08)

        # Loan payments (monthly)
        loan_out = monthly_loan_payments

        # Net for the month
        net = revenue_in - costs_out - loan_out
        cumulative_cash += net

        if cumulative_cash < lowest_balance:
            lowest_balance = cumulative_cash

        is_stress = net < 0
        if is_stress:
            total_negative_months += 1
            stress_months.append({
                "month": m,
                "name": MONTH_NAMES[m],
                "revenue_in": round(revenue_in),
                "costs_out": round(costs_out),
                "loan_out": round(loan_out),
                "net_cash": round(net),
                "cumulative_balance": round(cumulative_cash),
            })

        months.append({
            "month": m,
            "name": MONTH_NAMES[m],
            "revenue_in": round(revenue_in),
            "costs_out": round(costs_out),
            "loan_out": round(loan_out),
            "net_cash": round(net),
            "cumulative_balance": round(cumulative_cash),
        })

    # Liquidity metrics
    working_capital_needed = abs(min(0, lowest_balance))
    can_meet_obligations = cumulative_cash > 0
    worst_month = min(months, key=lambda m: m["net_cash"])

    # Overall assessment
    if total_negative_months == 0:
        liquidity_rating = "Strong - positive cash flow every month"
    elif total_negative_months <= 3 and can_meet_obligations:
        liquidity_rating = "Adequate - seasonal stress but reserves sufficient"
    elif total_negative_months <= 6 and can_meet_obligations:
        liquidity_rating = "Seasonal - significant pre-harvest cash burn. Reserves needed."
    elif can_meet_obligations:
        liquidity_rating = "Stretched - most months negative. Requires substantial reserves."
    else:
        liquidity_rating = "Critical - projected to run out of cash. Working capital loan recommended."

    # What if commodity prices drop 20%?
    stress_revenue = annual_revenue * 0.80
    stress_cumulative = existing_cash_reserves
    stress_survives = True
    for m in range(1, 13):
        rev = stress_revenue * revenue_profile.get(m, 0.05) + (eu_cap_payment if m == cap_month else 0)
        cost = annual_opex * cost_profile.get(m, 0.08)
        stress_cumulative += rev - cost - monthly_loan_payments
        if stress_cumulative < -50000:
            stress_survives = False
            break

    logger.info(f"Liquidity stress test: {total_negative_months} negative months, "
                f"worst={worst_month['name']} ({worst_month['net_cash']:,.0f} kr), "
                f"rating={liquidity_rating.split(' -')[0]}")

    return {
        "monthly_cash_flows": months,
        "summary": {
            "annual_revenue": round(annual_revenue),
            "annual_opex": round(annual_opex),
            "monthly_loan_payments": round(monthly_loan_payments),
            "eu_cap_payment": round(eu_cap_payment),
            "existing_reserves": round(existing_cash_reserves),
            "total_negative_months": total_negative_months,
            "lowest_cumulative_balance": round(lowest_balance),
            "working_capital_needed": round(working_capital_needed),
            "can_meet_obligations": can_meet_obligations,
            "liquidity_rating": liquidity_rating,
        },
        "worst_month": worst_month,
        "stress_months": stress_months,
        "commodity_stress_test": {
            "scenario": "20% commodity price drop",
            "adjusted_revenue": round(stress_revenue),
            "survives_without_deficit": stress_survives,
            "recommendation": (
                "Reserves sufficient to absorb 20% price drop."
                if stress_survives else
                "Would require additional working capital under 20% price drop."
            ),
        },
    }
