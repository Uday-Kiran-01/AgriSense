"""
Investment Simulator - simulates investment decisions and their financial impact.

Answers Oscar's question:
"How can scenario analysis help farmers understand the consequences
 of different investment decisions?"

Supports 4 scenario categories:
  Financial: new loans, early repayment, working capital, refinancing
  Environmental: rainfall, drought, flood, temperature
  Market: commodity prices, fuel, fertilizer
  Operational: farm expansion, crop change, yield, machinery
"""
import json
import numpy as np

from ..logger import get_logger
from .financial_analysis import calculate_financial_ratios

logger = get_logger(__name__)

# ---- Scenario Categories ----
SCENARIO_CATEGORIES = {
    "financial": ["new_farm_loan", "new_tractor_loan", "new_equipment_loan",
                  "early_repayment", "working_capital_loan", "refinance",
                  "interest_rate_change"],
    "environmental": ["rainfall_change", "drought", "flood", "temperature_change"],
    "market": ["commodity_price", "fuel_price", "fertilizer_cost"],
    "operational": ["farm_expansion", "crop_change", "yield_change",
                    "new_machinery", "build_storage", "install_irrigation"],
}

# ---- Investment Presets (for the frontend) ----
INVESTMENT_PRESETS = {
    "buy_tractor": {
        "label": "Purchase a Tractor",
        "icon": "🚜",
        "category": "financial",
        "scenarios": [
            {"type": "new_tractor_loan", "params": {"tractor_cost": 850000, "loan_amount": 600000,
                                                     "interest_rate": 5.5, "tenure_months": 60}},
        ],
    },
    "buy_harvester": {
        "label": "Purchase a Harvester",
        "icon": "🌾",
        "category": "financial",
        "scenarios": [
            {"type": "new_equipment_loan", "params": {"equipment_cost": 1200000, "loan_amount": 900000,
                                                       "interest_rate": 5.0, "tenure_months": 72}},
        ],
    },
    "expand_farm": {
        "label": "Expand Farm by 20 Hectares",
        "icon": "🌍",
        "category": "operational",
        "scenarios": [
            {"type": "farm_expansion", "params": {"additional_hectares": 20, "land_cost_per_ha": 85000,
                                                   "loan_pct": 70, "interest_rate": 4.5, "tenure_months": 120}},
        ],
    },
    "install_irrigation": {
        "label": "Install Irrigation System",
        "icon": "💧",
        "category": "operational",
        "scenarios": [
            {"type": "install_irrigation", "params": {"system_cost": 350000, "loan_pct": 80,
                                                       "interest_rate": 5.0, "tenure_months": 48}},
        ],
    },
    "build_storage": {
        "label": "Build Storage Facility",
        "icon": "🏗️",
        "category": "operational",
        "scenarios": [
            {"type": "build_storage", "params": {"construction_cost": 500000, "loan_pct": 60,
                                                  "interest_rate": 4.8, "tenure_months": 84}},
        ],
    },
    "working_capital": {
        "label": "Take a Working Capital Loan",
        "icon": "💰",
        "category": "financial",
        "scenarios": [
            {"type": "working_capital_loan", "params": {"loan_amount": 200000, "interest_rate": 6.5,
                                                         "tenure_months": 24}},
        ],
    },
    "refinance": {
        "label": "Refinance Existing Loans",
        "icon": "🔄",
        "category": "financial",
        "scenarios": [
            {"type": "refinance", "params": {"new_rate": 4.2, "consolidate": True}},
        ],
    },
}


def _annuity(p: float, r: float, n: int) -> float:
    """Monthly payment for loan principal p, annual rate r%, n months."""
    monthly = r / 100 / 12
    if monthly == 0:
        return p / n
    return p * monthly * (1 + monthly) ** n / ((1 + monthly) ** n - 1)


def run_single_scenario(
    scenario_type: str,
    parameters: dict,
    financial_records: list[dict],
    existing_loans: list[dict],
    operational_data: dict | None,
) -> tuple[list[dict], list[dict], dict, str]:
    """
    Apply a single scenario to the financial state.
    Returns (modified_financials, modified_loans, modified_ops, scenario_name).
    """
    modified_financials = [dict(r) for r in financial_records]
    latest = modified_financials[-1]
    modified_loans = [dict(l) for l in existing_loans]
    modified_ops = dict(operational_data) if operational_data else {}
    scenario_name = scenario_type.replace("_", " ").title()

    # ---- FINANCIAL SCENARIOS ----

    if scenario_type == "new_farm_loan":
        amount = parameters.get("loan_amount", 500000)
        rate = parameters.get("interest_rate", 5.0)
        tenure = parameters.get("tenure_months", 120)
        emi = _annuity(amount, rate, tenure)
        modified_loans.append({
            "loan_type": "new_farm_loan", "outstanding_balance": amount,
            "monthly_emi": emi, "annual_debt_service": emi * 12,
            "interest_rate": rate, "on_time_payments": 0, "total_payments_due": 0,
        })
        latest["interest_expense"] += amount * rate / 100
        scenario_name = f"New Farm Loan {amount:,.0f} kr"

    elif scenario_type == "new_tractor_loan":
        cost = parameters.get("tractor_cost", 850000)
        amount = parameters.get("loan_amount", 600000)
        rate = parameters.get("interest_rate", 5.5)
        tenure = parameters.get("tenure_months", 60)
        emi = _annuity(amount, rate, tenure)
        modified_loans.append({
            "loan_type": "tractor_loan_new", "outstanding_balance": amount,
            "monthly_emi": emi, "annual_debt_service": emi * 12,
            "interest_rate": rate, "on_time_payments": 0, "total_payments_due": 0,
        })
        latest["fixed_assets"] += cost
        latest["total_assets"] += cost
        latest["depreciation"] += cost * 0.10
        latest["interest_expense"] += amount * rate / 100
        scenario_name = f"Tractor Purchase {cost:,.0f} kr"

    elif scenario_type == "new_equipment_loan":
        cost = parameters.get("equipment_cost", 500000)
        amount = parameters.get("loan_amount", 400000)
        rate = parameters.get("interest_rate", 5.0)
        tenure = parameters.get("tenure_months", 60)
        emi = _annuity(amount, rate, tenure)
        modified_loans.append({
            "loan_type": "equipment_loan_new", "outstanding_balance": amount,
            "monthly_emi": emi, "annual_debt_service": emi * 12,
            "interest_rate": rate, "on_time_payments": 0, "total_payments_due": 0,
        })
        latest["fixed_assets"] += cost
        latest["total_assets"] += cost
        latest["depreciation"] += cost * 0.12
        latest["interest_expense"] += amount * rate / 100
        scenario_name = f"Equipment Purchase {cost:,.0f} kr"

    elif scenario_type == "early_repayment":
        loan_index = parameters.get("loan_index", 0)
        amount = parameters.get("repayment_amount", 100000)
        if loan_index < len(modified_loans):
            modified_loans[loan_index]["outstanding_balance"] = max(
                0, modified_loans[loan_index]["outstanding_balance"] - amount
            )
            # Reduce EMI proportionally
            ratio = modified_loans[loan_index]["outstanding_balance"] / max(
                modified_loans[loan_index]["outstanding_balance"] + amount, 1
            )
            modified_loans[loan_index]["monthly_emi"] *= ratio
            modified_loans[loan_index]["annual_debt_service"] = modified_loans[loan_index]["monthly_emi"] * 12
            latest["current_assets"] -= amount  # cash used for repayment
        scenario_name = f"Early Repayment {amount:,.0f} kr"

    elif scenario_type == "working_capital_loan":
        amount = parameters.get("loan_amount", 200000)
        rate = parameters.get("interest_rate", 6.5)
        tenure = parameters.get("tenure_months", 24)
        emi = _annuity(amount, rate, tenure)
        modified_loans.append({
            "loan_type": "working_capital", "outstanding_balance": amount,
            "monthly_emi": emi, "annual_debt_service": emi * 12,
            "interest_rate": rate, "on_time_payments": 0, "total_payments_due": 0,
        })
        latest["current_assets"] += amount  # cash inflow
        latest["interest_expense"] += amount * rate / 100
        scenario_name = f"Working Capital {amount:,.0f} kr"

    elif scenario_type == "refinance":
        new_rate = parameters.get("new_rate", 4.2)
        for loan in modified_loans:
            loan["interest_rate"] = new_rate
        total_balance = sum(l["outstanding_balance"] for l in modified_loans)
        latest["interest_expense"] = total_balance * new_rate / 100
        # Recalculate EMIs
        for loan in modified_loans:
            if loan["outstanding_balance"] > 0:
                loan["monthly_emi"] = _annuity(loan["outstanding_balance"], new_rate, 120)
                loan["annual_debt_service"] = loan["monthly_emi"] * 12
        scenario_name = f"Refinance at {new_rate}%"

    elif scenario_type == "interest_rate_change":
        change = parameters.get("rate_change_pct", 2)
        for loan in modified_loans:
            old_rate = loan["interest_rate"]
            new_rate = old_rate + change
            loan["interest_rate"] = new_rate
            loan["monthly_emi"] *= (new_rate / old_rate) if old_rate > 0 else 1
            loan["annual_debt_service"] = loan["monthly_emi"] * 12
        latest["interest_expense"] *= (1 + change / 100)
        scenario_name = f"Interest Rate +{change}%"

    # ---- ENVIRONMENTAL SCENARIOS ----

    elif scenario_type == "rainfall_change":
        pct = parameters.get("rainfall_change_pct", -20)
        yield_impact = pct / 100 * 0.6
        latest["revenue"] *= (1 + yield_impact)
        latest["operating_cash_flow"] *= (1 + yield_impact * 0.4)
        scenario_name = f"Rainfall {pct:+d}%"

    elif scenario_type == "drought":
        severity = parameters.get("severity_pct", -30)
        latest["revenue"] *= (1 + severity / 100 * 0.7)
        latest["operating_cash_flow"] *= (1 + severity / 100 * 0.5)
        scenario_name = f"Drought Impact {severity}%"

    elif scenario_type == "flood":
        damage_pct = parameters.get("damage_pct", -15)
        latest["revenue"] *= (1 + damage_pct / 100)
        latest["fixed_assets"] *= (1 + damage_pct / 100 * 0.3)
        scenario_name = f"Flood Damage {abs(damage_pct)}%"

    elif scenario_type == "temperature_change":
        pct = parameters.get("temp_change_pct", -10)
        latest["revenue"] *= (1 + pct / 100 * 0.4)
        scenario_name = f"Temperature Impact {pct:+d}%"

    # ---- MARKET SCENARIOS ----

    elif scenario_type == "commodity_price":
        pct = parameters.get("price_change_pct", -15)
        yield_impact = pct / 100 * 0.7
        latest["revenue"] *= (1 + yield_impact)
        latest["operating_cash_flow"] *= (1 + yield_impact * 0.5)
        scenario_name = f"Commodity Price {pct:+d}%"

    elif scenario_type == "fuel_price":
        pct = parameters.get("fuel_price_change_pct", 15)
        latest["operating_expenses"] *= (1 + pct / 100 * 0.15)
        latest["operating_cash_flow"] *= (1 - pct / 100 * 0.05)
        scenario_name = f"Fuel Price +{pct}%"

    elif scenario_type == "fertilizer_cost":
        pct = parameters.get("fertilizer_change_pct", 20)
        latest["operating_expenses"] *= (1 + pct / 100 * 0.10)
        scenario_name = f"Fertilizer Cost +{pct}%"

    # ---- OPERATIONAL SCENARIOS ----

    elif scenario_type == "farm_expansion":
        additional_ha = parameters.get("additional_hectares", 20)
        land_cost = parameters.get("land_cost_per_ha", 85000) * additional_ha
        loan_pct = parameters.get("loan_pct", 70) / 100
        rate = parameters.get("interest_rate", 4.5)
        tenure = parameters.get("tenure_months", 120)

        loan_amount = land_cost * loan_pct
        emi = _annuity(loan_amount, rate, tenure)
        modified_loans.append({
            "loan_type": "land_acquisition", "outstanding_balance": loan_amount,
            "monthly_emi": emi, "annual_debt_service": emi * 12,
            "interest_rate": rate, "on_time_payments": 0, "total_payments_due": 0,
        })
        latest["fixed_assets"] += land_cost
        latest["total_assets"] += land_cost
        latest["interest_expense"] += loan_amount * rate / 100
        if modified_ops:
            modified_ops["farm_size_acres"] = modified_ops.get("farm_size_acres", 0) + additional_ha
            # Revenue scales with farm size
            rev_per_ha = latest["revenue"] / max(modified_ops["farm_size_acres"] - additional_ha, 1)
            latest["revenue"] += rev_per_ha * additional_ha * 0.7  # 70% efficiency on new land
        scenario_name = f"Farm Expansion +{additional_ha} ha"

    elif scenario_type == "crop_change":
        new_crop = parameters.get("new_crop", "Hostvete")
        yield_change = parameters.get("yield_change_pct", 10)
        price_factor = parameters.get("price_factor", 1.15)
        latest["revenue"] *= (1 + yield_change / 100) * price_factor
        if modified_ops:
            modified_ops["crop_type"] = new_crop
        scenario_name = f"Crop Change to {new_crop}"

    elif scenario_type == "yield_change":
        pct = parameters.get("yield_change_pct", 15)
        latest["revenue"] *= (1 + pct / 100)
        if modified_ops:
            modified_ops["crop_yield_kg"] = modified_ops.get("crop_yield_kg", 0) * (1 + pct / 100)
        scenario_name = f"Yield {'+' if pct > 0 else ''}{pct}%"

    elif scenario_type == "new_machinery":
        cost = parameters.get("machinery_cost", 400000)
        efficiency_gain = parameters.get("efficiency_gain_pct", 8)
        latest["fixed_assets"] += cost
        latest["total_assets"] += cost
        latest["depreciation"] += cost * 0.12
        latest["operating_expenses"] *= (1 - efficiency_gain / 100 * 0.3)
        if modified_ops:
            modified_ops["machinery_value"] = modified_ops.get("machinery_value", 0) + cost
        scenario_name = f"New Machinery {cost:,.0f} kr"

    elif scenario_type == "build_storage":
        cost = parameters.get("construction_cost", 500000)
        loan_pct = parameters.get("loan_pct", 60) / 100
        rate = parameters.get("interest_rate", 4.8)
        tenure = parameters.get("tenure_months", 84)

        loan_amount = cost * loan_pct
        emi = _annuity(loan_amount, rate, tenure)
        modified_loans.append({
            "loan_type": "storage_facility", "outstanding_balance": loan_amount,
            "monthly_emi": emi, "annual_debt_service": emi * 12,
            "interest_rate": rate, "on_time_payments": 0, "total_payments_due": 0,
        })
        latest["fixed_assets"] += cost
        latest["total_assets"] += cost
        latest["depreciation"] += cost * 0.05
        latest["interest_expense"] += loan_amount * rate / 100
        # Storage reduces post-harvest losses
        latest["revenue"] *= 1.04  # 4% less waste
        scenario_name = f"Storage Facility {cost:,.0f} kr"

    elif scenario_type == "install_irrigation":
        cost = parameters.get("system_cost", 350000)
        loan_pct = parameters.get("loan_pct", 80) / 100
        rate = parameters.get("interest_rate", 5.0)
        tenure = parameters.get("tenure_months", 48)

        loan_amount = cost * loan_pct
        emi = _annuity(loan_amount, rate, tenure)
        modified_loans.append({
            "loan_type": "irrigation_system", "outstanding_balance": loan_amount,
            "monthly_emi": emi, "annual_debt_service": emi * 12,
            "interest_rate": rate, "on_time_payments": 0, "total_payments_due": 0,
        })
        latest["fixed_assets"] += cost
        latest["total_assets"] += cost
        latest["depreciation"] += cost * 0.08
        latest["interest_expense"] += loan_amount * rate / 100
        # Irrigation improves yield stability
        latest["revenue"] *= 1.08
        if modified_ops:
            modified_ops["has_irrigation"] = True
        scenario_name = f"Irrigation System {cost:,.0f} kr"

    else:
        # Legacy compatibility
        return _run_legacy_scenario(scenario_type, parameters, modified_financials,
                                     modified_loans, modified_ops)

    # Recalculate net income after all modifications
    latest["net_income"] = (latest["revenue"] - latest["operating_expenses"]
                            - latest["interest_expense"] - latest["depreciation"])

    return modified_financials, modified_loans, modified_ops, scenario_name


def _run_legacy_scenario(scenario_type, params, financials, loans, ops):
    """Handle old scenario types for backward compatibility."""
    name_map = {
        "rainfall": "rainfall_change", "commodity": "commodity_price",
        "new_loan": "new_farm_loan", "interest": "interest_rate_change",
        "fuel": "fuel_price", "tractor_purchase": "new_tractor_loan",
    }
    mapped = name_map.get(scenario_type)
    if mapped:
        return run_single_scenario(mapped, params, financials, loans, ops)
    return financials, loans, ops, f"Unknown: {scenario_type}"


def run_combined_scenarios(
    scenarios: list[dict],
    financial_records: list[dict],
    existing_loans: list[dict],
    operational_data: dict | None,
    base_ratios: dict,
) -> dict:
    """
    Run multiple scenarios combined and produce a full comparison.
    This is the main entry point for the Investment Simulator.

    scenarios = [
        {"type": "new_tractor_loan", "params": {...}},
        {"type": "commodity_price", "params": {...}},
    ]
    """
    fin = [dict(r) for r in financial_records]
    loans = [dict(l) for l in existing_loans]
    ops = dict(operational_data) if operational_data else {}
    scenario_names = []
    all_params = {}

    for s in scenarios:
        s_type = s["type"]
        s_params = s.get("params", {})
        fin, loans, ops, name = run_single_scenario(s_type, s_params, fin, loans, ops)
        scenario_names.append(name)
        all_params[s_type] = s_params

    combined_name = " + ".join(scenario_names)

    # Recalculate ALL metrics after combined scenarios
    new_ratios = calculate_financial_ratios(fin, loans, ops)

    # Build comprehensive before/after comparison
    old_dti = base_ratios.get("debt_to_income", 0)
    new_dti = new_ratios.get("debt_to_income", 0)
    old_dscr = base_ratios.get("dscr", 1)
    new_dscr = new_ratios.get("dscr", 1)

    # Determine overall change
    if new_dti > old_dti * 1.15 or new_dscr < old_dscr * 0.85:
        risk_change = "worsened"
    elif new_dti < old_dti * 0.85 and new_dscr > old_dscr * 1.15:
        risk_change = "improved"
    else:
        risk_change = "unchanged"

    # Full comparison table
    old_debt = sum(l.get("outstanding_balance", 0) for l in existing_loans)
    new_debt = sum(l.get("outstanding_balance", 0) for l in loans)
    old_emi = sum(l.get("monthly_emi", 0) for l in existing_loans)
    new_emi = sum(l.get("monthly_emi", 0) for l in loans)

    comparison = {
        "scenario_name": combined_name,
        "scenarios_applied": [{"type": s["type"], "name": n}
                              for s, n in zip(scenarios, scenario_names)],

        "before": {
            "existing_debt": round(old_debt),
            "monthly_emi": round(old_emi),
            "annual_debt_service": round(old_emi * 12),
            "debt_to_income": round(old_dti, 4),
            "dscr": round(old_dscr, 2),
            "working_capital": round(base_ratios.get("working_capital", 0)),
            "operating_margin": round(base_ratios.get("operating_margin", 0), 4),
            "loan_to_value": round(base_ratios.get("loan_to_value", 0), 4),
            "operating_cash_flow": round(financial_records[-1].get("operating_cash_flow", 0)),
            "revenue": round(financial_records[-1].get("revenue", 0)),
            "net_income": round(financial_records[-1].get("net_income", 0)),
            "recommendation": base_ratios.get("recommendation_category", {}).get("category", "N/A"),
        },

        "after": {
            "existing_debt": round(new_debt),
            "monthly_emi": round(new_emi),
            "annual_debt_service": round(new_emi * 12),
            "debt_to_income": round(new_dti, 4),
            "dscr": round(new_dscr, 2),
            "working_capital": round(new_ratios.get("working_capital", 0)),
            "operating_margin": round(new_ratios.get("operating_margin", 0), 4),
            "loan_to_value": round(new_ratios.get("loan_to_value", 0), 4),
            "operating_cash_flow": round(fin[-1].get("operating_cash_flow", 0)),
            "revenue": round(fin[-1].get("revenue", 0)),
            "net_income": round(fin[-1].get("net_income", 0)),
            "recommendation": new_ratios.get("recommendation_category", {}).get("category", "N/A"),
        },

        "changes": {
            "existing_debt": round(new_debt - old_debt),
            "monthly_emi": round(new_emi - old_emi),
            "debt_to_income": round(new_dti - old_dti, 4),
            "dscr": round(new_dscr - old_dscr, 2),
            "working_capital": round(new_ratios.get("working_capital", 0) - base_ratios.get("working_capital", 0)),
            "revenue": round(fin[-1].get("revenue", 0) - financial_records[-1].get("revenue", 0)),
            "net_income": round(fin[-1].get("net_income", 0) - financial_records[-1].get("net_income", 0)),
        },

        "risk_change": risk_change,
        "recommendation": _generate_investment_narrative(
            combined_name, risk_change, old_dti, new_dti, old_dscr, new_dscr,
            round(new_debt - old_debt), round(new_emi - old_emi),
        ),
    }

    logger.info(f"Investment Simulator: '{combined_name}' - "
                f"DTI {old_dti:.1%}→{new_dti:.1%}, DSCR {old_dscr:.2f}→{new_dscr:.2f}, "
                f"risk={risk_change}")

    return comparison


def _generate_investment_narrative(
    name: str, risk_change: str,
    old_dti: float, new_dti: float,
    old_dscr: float, new_dscr: float,
    debt_change: float, emi_change: float,
) -> str:
    """Generate a clear narrative about the investment impact."""

    dti_delta = new_dti - old_dti
    dscr_delta = new_dscr - old_dscr

    if risk_change == "improved":
        return (
            f"✅ {name} improves the farm's financial position. "
            f"Debt-to-Income decreases from {old_dti:.1%} to {new_dti:.1%} "
            f"and DSCR improves from {old_dscr:.2f}x to {new_dscr:.2f}x. "
            f"This investment strengthens repayment capacity."
        )
    elif risk_change == "worsened":
        if new_dscr < 1.25:
            return (
                f"⚠️ {name} significantly increases financial risk. "
                f"DSCR drops from {old_dscr:.2f}x to {new_dscr:.2f}x - below the 1.25x minimum. "
                f"Monthly debt service increases by {emi_change:+,.0f} kr. "
                f"Consider a smaller loan, longer tenure, or additional collateral."
            )
        elif new_dscr < 1.50:
            return (
                f"⚠️ {name} increases debt burden. "
                f"DSCR decreases from {old_dscr:.2f}x to {new_dscr:.2f}x "
                f"and Debt-to-Income rises from {old_dti:.1%} to {new_dti:.1%}. "
                f"Monthly obligations increase by {emi_change:+,.0f} kr. "
                f"The farm remains viable but with reduced margin. "
                f"Crop insurance or partial collateral is recommended."
            )
        else:
            return (
                f"📊 {name} increases total debt by {debt_change:+,.0f} kr. "
                f"DSCR remains healthy at {new_dscr:.2f}x despite the additional obligation. "
                f"The farm can absorb this investment while maintaining adequate coverage."
            )
    else:
        return (
            f"➡️ {name} has minimal impact on the farm's financial position. "
            f"DTI remains at {new_dti:.1%} with DSCR at {new_dscr:.2f}x. "
            f"The farm's financing capacity is stable."
        )
