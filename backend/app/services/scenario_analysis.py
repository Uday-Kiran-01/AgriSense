"""
Scenario Analysis Engine — simulates "what-if" scenarios.
"""
import json

import numpy as np

from ..logger import get_logger
from .financial_analysis import calculate_financial_ratios

logger = get_logger(__name__)


def run_scenario(
    scenario_type: str,
    parameters: dict,
    financial_records: list[dict],
    existing_loans: list[dict],
    operational_data: dict | None,
    base_ratios: dict,
) -> dict:
    """
    Run a what-if scenario by modifying input parameters and recalculating.

    Supported scenarios:
    - rainfall: {rainfall_change_pct: -20}
    - commodity: {price_change_pct: -15}
    - new_loan: {loan_amount: 200000, interest_rate: 10, tenure_months: 36}
    - interest: {rate_change_pct: +2}
    - fuel: {fuel_price_change_pct: +15}
    - tractor_purchase: {tractor_cost: 500000, loan_amount: 400000, interest_rate: 8}
    """
    # Deep copy financial records to avoid mutation
    modified_financials = [dict(r) for r in financial_records]
    latest = modified_financials[-1]  # most recent year
    modified_loans = [dict(l) for l in existing_loans]
    modified_ops = dict(operational_data) if operational_data else {}

    scenario_name = scenario_type.replace("_", " ").title()

    if scenario_type == "rainfall":
        pct = parameters.get("rainfall_change_pct", -20)
        # Affect revenue through yield impact
        yield_impact = pct / 100 * 0.6  # 60% pass-through to revenue
        latest["revenue"] *= (1 + yield_impact)
        latest["net_income"] = latest["revenue"] - latest["operating_expenses"] - latest["interest_expense"] - latest["depreciation"]
        latest["operating_cash_flow"] *= (1 + yield_impact * 0.4)
        scenario_name = f"Rainfall {pct:+d}%"

    elif scenario_type == "commodity":
        pct = parameters.get("price_change_pct", -15)
        yield_impact = pct / 100 * 0.7  # 70% pass-through
        latest["revenue"] *= (1 + yield_impact)
        latest["net_income"] = latest["revenue"] - latest["operating_expenses"] - latest["interest_expense"] - latest["depreciation"]
        latest["operating_cash_flow"] *= (1 + yield_impact * 0.5)
        scenario_name = f"Commodity Price {pct:+d}%"

    elif scenario_type == "new_loan":
        amount = parameters.get("loan_amount", 200000)
        rate = parameters.get("interest_rate", 10)
        tenure = parameters.get("tenure_months", 36)

        # Calculate monthly EMI (flat formula)
        monthly_rate = rate / 100 / 12
        if monthly_rate > 0:
            emi = amount * monthly_rate * (1 + monthly_rate) ** tenure / ((1 + monthly_rate) ** tenure - 1)
        else:
            emi = amount / tenure

        modified_loans.append({
            "loan_type": "new_loan",
            "outstanding_balance": amount,
            "monthly_emi": emi,
            "annual_debt_service": emi * 12,
            "interest_rate": rate,
            "on_time_payments": 0,
            "total_payments_due": 0,
        })
        scenario_name = f"New Loan ₹{amount:,.0f}"

    elif scenario_type == "interest":
        rate_change = parameters.get("rate_change_pct", 2)
        # Apply rate increase to all existing floating-rate loans
        for loan in modified_loans:
            old_rate = loan["interest_rate"]
            new_rate = old_rate + rate_change
            loan["interest_rate"] = new_rate
            # Recalculate EMI proportionally
            loan["monthly_emi"] *= (new_rate / old_rate)
            loan["annual_debt_service"] = loan["monthly_emi"] * 12
        # Update interest expense
        latest["interest_expense"] *= (1 + rate_change / 100)
        latest["net_income"] = latest["revenue"] - latest["operating_expenses"] - latest["interest_expense"] - latest["depreciation"]
        scenario_name = f"Interest Rate +{rate_change}%"

    elif scenario_type == "fuel":
        pct = parameters.get("fuel_price_change_pct", 15)
        # Fuel affects operating expenses
        latest["operating_expenses"] *= (1 + pct / 100 * 0.15)  # 15% of opex is fuel
        latest["net_income"] = latest["revenue"] - latest["operating_expenses"] - latest["interest_expense"] - latest["depreciation"]
        latest["operating_cash_flow"] *= (1 - pct / 100 * 0.05)
        scenario_name = f"Fuel Price +{pct}%"

    elif scenario_type == "tractor_purchase":
        cost = parameters.get("tractor_cost", 500000)
        loan_amount = parameters.get("loan_amount", 400000)
        rate = parameters.get("interest_rate", 8)
        tenure = parameters.get("tenure_months", 60)

        monthly_rate = rate / 100 / 12
        emi = loan_amount * monthly_rate * (1 + monthly_rate) ** tenure / ((1 + monthly_rate) ** tenure - 1)

        modified_loans.append({
            "loan_type": "tractor_loan_new",
            "outstanding_balance": loan_amount,
            "monthly_emi": emi,
            "annual_debt_service": emi * 12,
            "interest_rate": rate,
            "on_time_payments": 0,
            "total_payments_due": 0,
        })
        # Increase fixed assets and depreciation
        latest["fixed_assets"] += cost
        latest["total_assets"] += cost
        latest["depreciation"] += cost * 0.10  # 10% annual depreciation
        latest["net_income"] = latest["revenue"] - latest["operating_expenses"] - latest["interest_expense"] - latest["depreciation"]
        scenario_name = f"Tractor Purchase ₹{cost:,.0f}"

    else:
        return {"error": f"Unknown scenario type: {scenario_type}"}

    # Recalculate ratios
    new_ratios = calculate_financial_ratios(modified_financials, modified_loans, modified_ops)

    # Compare with baseline
    risk_change = "unchanged"
    old_dti = base_ratios.get("debt_to_income", 0)
    new_dti = new_ratios.get("debt_to_income", 0)

    if new_dti > old_dti * 1.15:
        risk_change = "worsened"
    elif new_dti < old_dti * 0.85:
        risk_change = "improved"

    logger.info(f"Scenario '{scenario_name}': risk {risk_change}, "
                f"DTI {old_dti:.2%} → {new_dti:.2%}")

    return {
        "scenario_name": scenario_name,
        "scenario_type": scenario_type,
        "parameters": parameters,
        "new_ratios": new_ratios,
        "risk_change": risk_change,
        "recommendation": _generate_recommendation(scenario_type, risk_change, new_ratios),
    }


def _generate_recommendation(scenario_type: str, risk_change: str, ratios: dict) -> str:
    """Generate a plain-English recommendation based on scenario results."""
    dscr = ratios.get("dscr", 1)
    dti = ratios.get("debt_to_income", 0)

    if risk_change == "worsened":
        if dscr < 1.25:
            return (f"⚠️ DSCR drops to {dscr:.2f}x — below the 1.25x minimum. "
                    "Additional financing would be risky. Consider crop insurance or reducing existing debt first.")
        return (f"⚠️ Risk profile worsens. DTI rises to {dti:.1%}. "
                "Proceed with caution. Mitigation measures recommended.")

    if risk_change == "improved":
        return (f"✅ Financial position improves. DTI at {dti:.1%} with DSCR of {dscr:.2f}x. "
                "Additional capacity available for financing.")

    return (f"➡️ Minimal impact on financial position. DTI remains at {dti:.1%} with DSCR of {dscr:.2f}x. "
            "Current financing capacity is stable.")
