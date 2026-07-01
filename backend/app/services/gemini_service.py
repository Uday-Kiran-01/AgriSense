"""
Gemini AI Service - handles document summarization, metric explanations,
and decision memo generation. Gemini NEVER makes lending decisions.
"""
import google.generativeai as genai

from ..config import settings
from ..logger import get_logger

logger = get_logger(__name__)

# Configure Gemini if API key is available
gemini_model = None
if settings.gemini_available:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel("gemini-1.5-flash")
    logger.info("Gemini AI configured")
else:
    logger.warning("Gemini API key not set - using fallback text generation")


def _generate(prompt: str, fallback: str = "") -> str:
    """Call Gemini or return fallback."""
    if gemini_model:
        try:
            response = gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return fallback or f"[Gemini unavailable: {e}]"
    return fallback or "[Gemini API key not configured. Set GEMINI_API_KEY in .env]"


def explain_financial_metric(metric_name: str, value: float, farmer_name: str = "the farmer") -> str:
    """
    Explain a financial metric in plain English for a farmer.
    """
    prompt = f"""You are an agricultural finance advisor explaining financial concepts to a farmer named {farmer_name}.

Explain the financial metric "{metric_name}" with value {value} in simple terms.
- Use an analogy a farmer would understand
- Explain what a good value looks like
- Keep it under 3 sentences
- Do NOT make any lending recommendations
"""
    fallback = _rule_based_explanation(metric_name, value)
    return _generate(prompt, fallback)


def _rule_based_explanation(metric_name: str, value: float) -> str:
    """Fallback rule-based explanations when Gemini is unavailable."""
    explanations = {
        "debt_to_income": (
            f"For every ₹100 earned, ₹{value * 100:.0f} goes toward loan payments. "
            f"Below 40% is comfortable; above 50% is tight. "
            f"Think of it like setting aside grain for the mill - you need enough left for your household."
        ),
        "dscr": (
            f"The farm generates ₹{value:.1f} for every ₹1 of loan payment due. "
            f"Above 1.5 means comfortable coverage; below 1.25 means tight. "
            f"It's like having enough fodder reserves - you want a buffer, not just enough."
        ),
        "operating_margin": (
            f"After all expenses, {value * 100:.0f}% of revenue remains as profit. "
            f"Above 25% is healthy for farming. "
            f"Like crop yield per acre - higher is better, and consistency matters."
        ),
        "loan_to_value": (
            f"Outstanding loans are {value * 100:.0f}% of total assets. "
            f"Below 50% is comfortable. "
            f"It's like how much of your land is mortgaged - less is safer."
        ),
    }
    return explanations.get(metric_name, f"{metric_name} is {value}. Consult a financial advisor for interpretation.")


def generate_decision_memo(
    farmer_name: str,
    financial_summary: dict,
    existing_loans: list[dict],
    external_risks: dict,
    financial_ratios: dict,
    ml_prediction: dict,
    scenarios: list[dict],
) -> dict:
    """
    Generate a structured decision memo using Gemini.
    Returns a dict with each section of the memo.
    """
    # Build context for Gemini
    context = f"""
FARMER: {farmer_name}

FINANCIAL SUMMARY (most recent year):
- Revenue: {financial_summary.get('revenue', 0):,.0f} kr
- Net Income: {financial_summary.get('net_income', 0):,.0f} kr
- Total Assets: {financial_summary.get('total_assets', 0):,.0f} kr
- Operating Cash Flow: {financial_summary.get('operating_cash_flow', 0):,.0f} kr

EXISTING LOANS:
{_format_loans(existing_loans)}

FINANCIAL RATIOS:
- Debt-to-Income: {financial_ratios.get('debt_to_income', 0):.1%}
- DSCR: {financial_ratios.get('dscr', 0):.2f}x
- Operating Margin: {financial_ratios.get('operating_margin', 0):.1%}
- Loan-to-Value: {financial_ratios.get('loan_to_value', 0):.1%}
- Current Ratio: {financial_ratios.get('current_ratio', 0):.2f}x
- Asset Coverage: {financial_ratios.get('asset_coverage', 0):.2f}x
- Working Capital: {financial_ratios.get('working_capital', 0):,.0f} kr

EXTERNAL RISKS:
- Weather: {external_risks.get('weather', {})}
- Commodity: {external_risks.get('commodity', {})}
- Fuel: {external_risks.get('fuel', {})}

ML PREDICTION:
- Credit Risk: {ml_prediction.get('credit_risk_score', 0):.0%} (0=low risk, 1=high risk)
- Repayment Probability: {ml_prediction.get('repayment_probability', 0):.0%}
- Additional Debt Capacity: {ml_prediction.get('debt_capacity', 0):,.0f} kr
- Financial Health Risk: {ml_prediction.get('financial_health_risk', 'N/A')}
- Environmental Risk: {ml_prediction.get('environmental_risk', 'N/A')}
- Market Risk: {ml_prediction.get('market_risk', 'N/A')}
- Overall Risk: {ml_prediction.get('overall_financing_risk', 'N/A')}

IMPORTANT: You are an AI assistant helping generate a decision memo. You do NOT make lending decisions.
The final decision is always made by a human loan officer. All currency values are in SEK.
This is a Swedish agricultural context. Use Swedish/EU terminology where appropriate. Data is synthetic.
"""

    sections = {}

    # 1. Financial Summary
    sections["financial_summary"] = _generate(
        f"{context}\n\nWrite a 3-4 sentence plain-English summary of this farmer's financial position. "
        "Highlight trends, strengths, and any concerns. Be objective.",
        _fallback_summary(farmer_name, financial_summary),
    )

    # 2. Existing Loans
    sections["existing_loans_summary"] = _generate(
        f"{context}\n\nSummarize the farmer's existing loan situation in 2-3 sentences. "
        "Note repayment history, total obligations, and whether the debt load appears manageable.",
        _fallback_loans(existing_loans),
    )

    # 3. External Risks
    sections["external_risks_summary"] = _generate(
        f"{context}\n\nSummarize the environmental and market risks in 2-3 sentences. "
        "Mention weather conditions, commodity price trends, and input costs.",
        _fallback_risks(external_risks),
    )

    # 4. Recommendation
    sections["recommendation"] = _generate(
        f"{context}\n\nBased on ALL the data above, write a 3-4 sentence overall assessment. "
        "Note: this is a decision-support recommendation, NOT a final lending decision. "
        "Summarize the key evidence supporting or cautioning against additional financing. "
        "Use phrases like 'the data suggests' or 'the analysis indicates' - never 'I approve' or 'I deny'.",
        _fallback_recommendation(ml_prediction),
    )

    # 5. Supporting Evidence
    sections["supporting_evidence"] = _generate(
        f"{context}\n\nList 4-5 bullet points of key evidence from the analysis "
        "that support the assessment. Each bullet should reference specific data.",
        _fallback_evidence(financial_ratios, ml_prediction),
    )

    # Combine into full memo
    sections["full_memo"] = f"""
{'='*60}
                DECISION MEMO - {farmer_name}
{'='*60}

FINANCIAL SUMMARY
{'-'*40}
{sections['financial_summary']}

EXISTING LOANS
{'-'*40}
{sections['existing_loans_summary']}

EXTERNAL RISK ASSESSMENT
{'-'*40}
{sections['external_risks_summary']}

OVERALL ASSESSMENT
{'-'*40}
{sections['recommendation']}

SUPPORTING EVIDENCE
{'-'*40}
{sections['supporting_evidence']}

{'='*60}
Generated by AgriSense AI | For human review only
{'='*60}
"""

    logger.info(f"Decision memo generated for {farmer_name}")
    return sections


# ---- Fallback generators (when Gemini is unavailable) ----

def _format_loans(loans: list[dict]) -> str:
    lines = []
    for l in loans:
        loan_type = l.get('loan_type', 'Loan').replace('_', ' ').title()
        # Translate loan types to Swedish display
        translations = {
            'Farm Loan': 'Jordbrukskredit',
            'Tractor Loan': 'Traktorlan',
            'Credit Line': 'Kreditlimit',
            'Equipment Loan': 'Utrustningslan',
            'Mortgage': 'Fastighetslan',
        }
        display_type = translations.get(loan_type, loan_type)
        lines.append(
            f"  - {display_type}: "
            f"{l.get('outstanding_balance', 0):,.0f} kr outstanding, "
            f"{l.get('monthly_emi', 0):,.0f} kr/month amortering"
        )
    return "\n".join(lines) if lines else "  No existing loans"


def _fallback_summary(name: str, fin: dict) -> str:
    revenue = fin.get("revenue", 0)
    net = fin.get("net_income", 0)
    return (
        f"{name} operates with annual revenue of approximately {revenue:,.0f} kr "
        f"and net income of {net:,.0f} kr. The farm shows steady operational performance "
        f"with adequate asset backing. Cash flow generation is positive, indicating "
        f"the farm can service its existing obligations."
    )


def _fallback_loans(loans: list[dict]) -> str:
    if not loans:
        return "No existing loans. The farmer has no current debt obligations."
    total = sum(l.get("outstanding_balance", 0) for l in loans)
    total_emi = sum(l.get("monthly_emi", 0) for l in loans)
    return (
        f"The farmer has {len(loans)} active loan(s) with total outstanding debt of "
        f"{total:,.0f} kr and a combined monthly amortering of {total_emi:,.0f} kr. "
        f"The repayment track record is generally positive."
    )


def _fallback_risks(risks: dict) -> str:
    weather = risks.get("weather", {})
    commodity = risks.get("commodity", {})
    drought = weather.get("drought_index", 0)
    flood = weather.get("flood_risk", "low")
    temp = weather.get("temperature_celsius", 8)
    return (
        f"Weather conditions show {'favorable' if drought < 0.3 else 'moderate'} "
        f"precipitation with {'low' if flood == 'low' else 'some'} flood risk. "
        f"Temperature averages {temp:.0f} C. "
        f"Commodity prices have changed {commodity.get('price_change_pct', 0):+.1f}% recently. "
        f"Input costs remain at typical Swedish levels."
    )


def _fallback_recommendation(pred: dict) -> str:
    risk = pred.get("overall_financing_risk", "medium")
    repay = pred.get("repayment_probability", 0.5)
    capacity = pred.get("debt_capacity", 0)

    if risk == "low":
        return (
            f"The analysis indicates strong financial health with a {repay:.0%} repayment probability. "
            f"Estimated additional debt capacity of {capacity:,.0f} kr. "
            f"The data suggests the farmer is well-positioned to consider additional financing, "
            f"subject to standard credit policies and human review."
        )
    elif risk == "high":
        return (
            f"The analysis indicates elevated risk with a {repay:.0%} repayment probability. "
            f"Estimated additional debt capacity of {capacity:,.0f} kr. "
            f"The data suggests caution - improving DSCR or reducing existing debt before additional "
            f"financing would strengthen the application. Final decision rests with the loan officer."
        )
    else:
        return (
            f"The analysis indicates moderate risk with a {repay:.0%} repayment probability. "
            f"Estimated additional debt capacity of {capacity:,.0f} kr. "
            f"The data suggests conditional consideration - mitigation measures such as crop insurance "
            f"or partial collateral may improve the risk profile. Human review required."
        )


def _fallback_evidence(ratios: dict, pred: dict) -> str:
    return (
        f"* DSCR of {ratios.get('dscr', 0):.2f}x - {'above' if ratios.get('dscr', 0) > 1.25 else 'below'} the 1.25x minimum threshold\n"
        f"* Debt-to-Income ratio of {ratios.get('debt_to_income', 0):.1%} - "
        f"{'manageable' if ratios.get('debt_to_income', 0) < 0.5 else 'elevated'}\n"
        f"* Loan-to-Value ratio of {ratios.get('loan_to_value', 0):.1%} - "
        f"{'strong collateral position' if ratios.get('loan_to_value', 0) < 0.5 else 'moderate'}\n"
        f"* Working capital of {ratios.get('working_capital', 0):,.0f} kr - "
        f"{'adequate liquidity' if ratios.get('working_capital', 0) > 0 else 'liquidity concern'}\n"
        f"* Model confidence: {pred.get('model_confidence', 0):.0%} - {pred.get('overall_financing_risk', 'N/A')} risk classification"
    )
