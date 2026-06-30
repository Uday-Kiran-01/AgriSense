"""
AgriSense API Router — all endpoints for the platform.
"""
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    Farmer, Document, ExistingLoan, FinancialRecord,
    OperationalData, ExternalData, Prediction,
    ScenarioResult, DecisionMemo,
)
from ..schemas import (
    FarmerCreate, FarmerRead,
    LoanCreate, LoanRead,
    FinancialRecordCreate, FinancialRecordRead,
    OperationalDataCreate, OperationalDataRead,
    PredictionRead,
    ScenarioRequest, ScenarioResultRead,
    DecisionMemoRead, FullProfile,
)
from ..services.financial_analysis import calculate_financial_ratios
from ..services.ml_service import engineer_features, predict
from ..services.scenario_analysis import run_scenario
from ..services.gemini_service import generate_decision_memo, explain_financial_metric
from ..services.external_data import get_all_external_data
from ..logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["AgriSense"])


# ---------------------------------------------------------------------------
# Farmer
# ---------------------------------------------------------------------------
@router.post("/farmers", response_model=FarmerRead, status_code=201)
def create_farmer(data: FarmerCreate, db: Session = Depends(get_db)):
    farmer = Farmer(**data.model_dump())
    db.add(farmer)
    db.commit()
    db.refresh(farmer)
    logger.info(f"Farmer created: {farmer.full_name} (id={farmer.id})")
    return farmer


@router.get("/farmers/{farmer_id}", response_model=FarmerRead)
def get_farmer(farmer_id: int, db: Session = Depends(get_db)):
    farmer = db.get(Farmer, farmer_id)
    if not farmer:
        raise HTTPException(404, "Farmer not found")
    return farmer


@router.get("/farmers", response_model=list[FarmerRead])
def list_farmers(db: Session = Depends(get_db)):
    return db.query(Farmer).all()


# ---------------------------------------------------------------------------
# Existing Loans
# ---------------------------------------------------------------------------
@router.post("/loans", response_model=LoanRead, status_code=201)
def create_loan(data: LoanCreate, db: Session = Depends(get_db)):
    loan = ExistingLoan(**data.model_dump())
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return loan


@router.get("/farmers/{farmer_id}/loans", response_model=list[LoanRead])
def get_farmer_loans(farmer_id: int, db: Session = Depends(get_db)):
    return db.query(ExistingLoan).filter(ExistingLoan.farmer_id == farmer_id).all()


# ---------------------------------------------------------------------------
# Financial Records
# ---------------------------------------------------------------------------
@router.post("/financials", response_model=FinancialRecordRead, status_code=201)
def create_financial_record(data: FinancialRecordCreate, db: Session = Depends(get_db)):
    record = FinancialRecord(**data.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/farmers/{farmer_id}/financials", response_model=list[FinancialRecordRead])
def get_farmer_financials(farmer_id: int, db: Session = Depends(get_db)):
    return (
        db.query(FinancialRecord)
        .filter(FinancialRecord.farmer_id == farmer_id)
        .order_by(FinancialRecord.year.desc())
        .all()
    )


# ---------------------------------------------------------------------------
# Operational Data
# ---------------------------------------------------------------------------
@router.post("/operational", response_model=OperationalDataRead, status_code=201)
def create_operational_data(data: OperationalDataCreate, db: Session = Depends(get_db)):
    ops = OperationalData(**data.model_dump())
    db.add(ops)
    db.commit()
    db.refresh(ops)
    return ops


@router.get("/farmers/{farmer_id}/operational", response_model=list[OperationalDataRead])
def get_farmer_operational(farmer_id: int, db: Session = Depends(get_db)):
    return (
        db.query(OperationalData)
        .filter(OperationalData.farmer_id == farmer_id)
        .all()
    )


# ---------------------------------------------------------------------------
# External Data
# ---------------------------------------------------------------------------
@router.get("/external-data")
async def fetch_external_data(region: str = "Gujarat", commodity: str = "WHEAT"):
    """Fetch weather, commodity, and government data."""
    data = await get_all_external_data(region, commodity)
    return data


# ---------------------------------------------------------------------------
# Financial Analysis
# ---------------------------------------------------------------------------
@router.get("/farmers/{farmer_id}/financial-analysis")
def get_financial_analysis(farmer_id: int, db: Session = Depends(get_db)):
    """Calculate all financial ratios for a farmer."""
    financials = (
        db.query(FinancialRecord)
        .filter(FinancialRecord.farmer_id == farmer_id)
        .order_by(FinancialRecord.year.desc())
        .all()
    )
    loans = (
        db.query(ExistingLoan)
        .filter(ExistingLoan.farmer_id == farmer_id)
        .all()
    )
    ops = (
        db.query(OperationalData)
        .filter(OperationalData.farmer_id == farmer_id)
        .first()
    )

    if not financials:
        raise HTTPException(404, "No financial records found")

    ratios = calculate_financial_ratios(
        [r.__dict__ for r in financials],
        [l.__dict__ for l in loans],
        ops.__dict__ if ops else None,
    )

    # Include raw financial data for context
    return {
        "ratios": ratios,
        "latest_financial": financials[0].__dict__ if financials else None,
        "loan_count": len(loans),
    }


# ---------------------------------------------------------------------------
# ML Prediction
# ---------------------------------------------------------------------------
@router.get("/farmers/{farmer_id}/predict", response_model=PredictionRead)
async def run_prediction(farmer_id: int, db: Session = Depends(get_db)):
    """Run ML prediction and store results."""
    # Gather all data
    financials = (
        db.query(FinancialRecord)
        .filter(FinancialRecord.farmer_id == farmer_id)
        .order_by(FinancialRecord.year.desc())
        .all()
    )
    loans = (
        db.query(ExistingLoan)
        .filter(ExistingLoan.farmer_id == farmer_id)
        .all()
    )
    ops = (
        db.query(OperationalData)
        .filter(OperationalData.farmer_id == farmer_id)
        .first()
    )

    if not financials:
        raise HTTPException(404, "No financial records found for prediction")

    # Calculate ratios
    ratios = calculate_financial_ratios(
        [r.__dict__ for r in financials],
        [l.__dict__ for l in loans],
        ops.__dict__ if ops else None,
    )

    # Fetch external data
    external = await get_all_external_data()

    # Engineer features and predict
    features = engineer_features(
        ratios,
        external,
        ops.__dict__ if ops else None,
        [l.__dict__ for l in loans],
    )
    result = predict(features)

    # Store prediction
    prediction = Prediction(
        farmer_id=farmer_id,
        credit_risk_score=result["credit_risk_score"],
        repayment_probability=result["repayment_probability"],
        debt_capacity=result["debt_capacity"],
        model_confidence=result["model_confidence"],
        model_version=result["model_version"],
        feature_importance_json=json.dumps(result["feature_importance"]),
        financial_health_risk=result["financial_health_risk"],
        environmental_risk=result["environmental_risk"],
        market_risk=result["market_risk"],
        overall_financing_risk=result["overall_financing_risk"],
        input_features_json=json.dumps({k: float(v) for k, v in zip(
            ["debt_to_income", "dscr", "working_capital", "operating_margin",
             "loan_to_value", "asset_coverage", "current_ratio", "debt_to_equity",
             "cash_flow_margin", "interest_coverage", "repayment_ratio",
             "drought_index", "price_change", "farm_size", "has_insurance"],
            features[0],
        )}),
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    logger.info(f"Prediction stored for farmer {farmer_id}")
    return prediction


@router.get("/farmers/{farmer_id}/predictions", response_model=list[PredictionRead])
def get_predictions(farmer_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Prediction)
        .filter(Prediction.farmer_id == farmer_id)
        .order_by(Prediction.created_at.desc())
        .all()
    )


# ---------------------------------------------------------------------------
# Scenario Analysis (Investment Simulator)
# ---------------------------------------------------------------------------
@router.post("/scenarios")
async def run_scenario_analysis(req: ScenarioRequest, db: Session = Depends(get_db)):
    """Run a single what-if scenario."""
    from ..services.scenario_analysis import run_single_scenario

    financials = (
        db.query(FinancialRecord)
        .filter(FinancialRecord.farmer_id == req.farmer_id)
        .order_by(FinancialRecord.year.desc())
        .all()
    )
    loans = (
        db.query(ExistingLoan)
        .filter(ExistingLoan.farmer_id == req.farmer_id)
        .all()
    )
    ops = (
        db.query(OperationalData)
        .filter(OperationalData.farmer_id == req.farmer_id)
        .first()
    )

    if not financials:
        raise HTTPException(404, "No financial records found")

    base_ratios = calculate_financial_ratios(
        [r.__dict__ for r in financials],
        [l.__dict__ for l in loans],
        ops.__dict__ if ops else None,
    )

    modified_fin, modified_loans, modified_ops, name = run_single_scenario(
        req.scenario_type,
        req.parameters,
        [r.__dict__ for r in financials],
        [l.__dict__ for l in loans],
        ops.__dict__ if ops else None,
    )

    new_ratios = calculate_financial_ratios(modified_fin, modified_loans, modified_ops)

    risk_change = "unchanged"
    old_dti = base_ratios.get("debt_to_income", 0)
    new_dti = new_ratios.get("debt_to_income", 0)
    if new_dti > old_dti * 1.15:
        risk_change = "worsened"
    elif new_dti < old_dti * 0.85:
        risk_change = "improved"

    from ..services.scenario_analysis import _generate_investment_narrative
    narrative = _generate_investment_narrative(
        name, risk_change,
        base_ratios.get("debt_to_income", 0), new_ratios.get("debt_to_income", 0),
        base_ratios.get("dscr", 1), new_ratios.get("dscr", 1),
        sum(l.get("outstanding_balance", 0) for l in modified_loans) -
        sum(l.outstanding_balance for l in loans),
        sum(l.get("monthly_emi", 0) for l in modified_loans) -
        sum(l.monthly_emi for l in loans),
    )

    scenario = ScenarioResult(
        farmer_id=req.farmer_id,
        scenario_name=name,
        scenario_type=req.scenario_type,
        parameters_json=json.dumps(req.parameters),
        new_debt_to_income=new_ratios.get("debt_to_income"),
        new_dscr=new_ratios.get("dscr"),
        risk_change=risk_change,
        recommendation=narrative,
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


# ---------------------------------------------------------------------------
# Investment Simulator (Combined Scenarios)
# ---------------------------------------------------------------------------
@router.post("/investment-simulator")
async def run_investment_simulator(
    farmer_id: int, scenarios: list[dict], db: Session = Depends(get_db),
):
    """
    Run multiple scenarios combined and return full before/after comparison.

    Body: { "farmer_id": 2501, "scenarios": [
        {"type": "new_tractor_loan", "params": {"tractor_cost": 850000, ...}},
        {"type": "commodity_price", "params": {"price_change_pct": -15}},
    ]}
    """
    from ..services.scenario_analysis import run_combined_scenarios

    financials = (
        db.query(FinancialRecord)
        .filter(FinancialRecord.farmer_id == farmer_id)
        .order_by(FinancialRecord.year.desc())
        .all()
    )
    loans = (
        db.query(ExistingLoan)
        .filter(ExistingLoan.farmer_id == farmer_id)
        .all()
    )
    ops = (
        db.query(OperationalData)
        .filter(OperationalData.farmer_id == farmer_id)
        .first()
    )

    if not financials:
        raise HTTPException(404, "No financial records found")

    base_ratios = calculate_financial_ratios(
        [r.__dict__ for r in financials],
        [l.__dict__ for l in loans],
        ops.__dict__ if ops else None,
    )

    result = run_combined_scenarios(
        scenarios,
        [r.__dict__ for r in financials],
        [l.__dict__ for l in loans],
        ops.__dict__ if ops else None,
        base_ratios,
    )

    # Store result
    combined_name = result["scenario_name"]
    scenario = ScenarioResult(
        farmer_id=farmer_id,
        scenario_name=combined_name,
        scenario_type="combined",
        parameters_json=json.dumps({"scenarios": result["scenarios_applied"]}),
        new_debt_to_income=result["after"]["debt_to_income"],
        new_dscr=result["after"]["dscr"],
        risk_change=result["risk_change"],
        recommendation=result["recommendation"],
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)

    return result


@router.get("/investment-presets")
def get_investment_presets():
    """Return available investment simulation presets."""
    from ..services.scenario_analysis import INVESTMENT_PRESETS
    return INVESTMENT_PRESETS


# ---------------------------------------------------------------------------
# Decision Readiness
# ---------------------------------------------------------------------------
@router.get("/farmers/{farmer_id}/decision-readiness")
def get_decision_readiness(farmer_id: int, db: Session = Depends(get_db)):
    """Assess whether enough evidence exists for a lending decision."""
    from ..services.decision_readiness import run_full_readiness_assessment

    farmer = db.get(Farmer, farmer_id)
    if not farmer:
        raise HTTPException(404, "Farmer not found")

    # Gather documents (metadata from seed)
    documents = [
        {"document_type": "financial_statement"},
        {"document_type": "bank_statement"},
        {"document_type": "loan_doc"},
        {"document_type": "land_record"},
        {"document_type": "farm_doc"},
        {"document_type": "insurance"},
    ]

    financials = (
        db.query(FinancialRecord)
        .filter(FinancialRecord.farmer_id == farmer_id)
        .order_by(FinancialRecord.year.desc())
        .all()
    )
    ops = (
        db.query(OperationalData)
        .filter(OperationalData.farmer_id == farmer_id)
        .first()
    )
    loans = (
        db.query(ExistingLoan)
        .filter(ExistingLoan.farmer_id == farmer_id)
        .all()
    )
    latest_pred = (
        db.query(Prediction)
        .filter(Prediction.farmer_id == farmer_id)
        .order_by(Prediction.created_at.desc())
        .first()
    )

    report = run_full_readiness_assessment(
        farmer_id,
        documents,
        [r.__dict__ for r in financials],
        [l.__dict__ for l in loans],
        ops.__dict__ if ops else None,
        model_confidence=latest_pred.model_confidence if latest_pred else None,
    )
    return report


# ---------------------------------------------------------------------------
# Liquidity Stress Test (Seasonal Cash Flow)
# ---------------------------------------------------------------------------
@router.get("/farmers/{farmer_id}/liquidity-stress-test")
def get_liquidity_stress_test(farmer_id: int, db: Session = Depends(get_db)):
    """Run seasonal cash flow analysis and liquidity stress test."""
    from ..services.liquidity_analysis import run_liquidity_stress_test

    financials = (
        db.query(FinancialRecord)
        .filter(FinancialRecord.farmer_id == farmer_id)
        .order_by(FinancialRecord.year.desc())
        .first()
    )
    loans = (
        db.query(ExistingLoan)
        .filter(ExistingLoan.farmer_id == farmer_id)
        .all()
    )
    ops = (
        db.query(OperationalData)
        .filter(OperationalData.farmer_id == farmer_id)
        .first()
    )

    if not financials:
        raise HTTPException(404, "No financial records found")

    annual_revenue = financials.revenue or 0
    annual_opex = financials.operating_expenses or 0
    crop = ops.crop_type if ops else "Mixed Grain"
    monthly_loans = sum(l.monthly_emi or 0 for l in loans)
    reserves = financials.current_assets - financials.current_liabilities if financials else 0

    result = run_liquidity_stress_test(
        annual_revenue=annual_revenue,
        annual_opex=annual_opex,
        crop_type=crop,
        monthly_loan_payments=monthly_loans,
        existing_cash_reserves=max(0, reserves),
        eu_cap_payment=115000,  # From external data
    )
    return result

    financials = (
        db.query(FinancialRecord)
        .filter(FinancialRecord.farmer_id == farmer_id)
        .order_by(FinancialRecord.year.desc())
        .all()
    )
    ops = (
        db.query(OperationalData)
        .filter(OperationalData.farmer_id == farmer_id)
        .first()
    )
    loans = (
        db.query(ExistingLoan)
        .filter(ExistingLoan.farmer_id == farmer_id)
        .all()
    )
    latest_pred = (
        db.query(Prediction)
        .filter(Prediction.farmer_id == farmer_id)
        .order_by(Prediction.created_at.desc())
        .first()
    )

    report = run_full_readiness_assessment(
        farmer_id,
        documents,
        [r.__dict__ for r in financials],
        [l.__dict__ for l in loans],
        ops.__dict__ if ops else None,
        n_conflicts=0,
        n_outliers=0,
        n_validation_errors=0,
        model_confidence=latest_pred.model_confidence if latest_pred else None,
    )
    return report


@router.get("/farmers/{farmer_id}/scenarios", response_model=list[ScenarioResultRead])
def get_scenarios(farmer_id: int, db: Session = Depends(get_db)):
    return (
        db.query(ScenarioResult)
        .filter(ScenarioResult.farmer_id == farmer_id)
        .order_by(ScenarioResult.created_at.desc())
        .all()
    )


# ---------------------------------------------------------------------------
# Decision Memo
# ---------------------------------------------------------------------------
@router.post("/farmers/{farmer_id}/decision-memo", response_model=DecisionMemoRead)
async def create_decision_memo(farmer_id: int, db: Session = Depends(get_db)):
    """Generate a full decision memo using Gemini AI."""
    farmer = db.get(Farmer, farmer_id)
    if not farmer:
        raise HTTPException(404, "Farmer not found")

    financials = (
        db.query(FinancialRecord)
        .filter(FinancialRecord.farmer_id == farmer_id)
        .order_by(FinancialRecord.year.desc())
        .all()
    )
    loans = (
        db.query(ExistingLoan)
        .filter(ExistingLoan.farmer_id == farmer_id)
        .all()
    )
    ops = (
        db.query(OperationalData)
        .filter(OperationalData.farmer_id == farmer_id)
        .first()
    )
    latest_prediction = (
        db.query(Prediction)
        .filter(Prediction.farmer_id == farmer_id)
        .order_by(Prediction.created_at.desc())
        .first()
    )

    if not financials:
        raise HTTPException(404, "No financial records")

    ratios = calculate_financial_ratios(
        [r.__dict__ for r in financials],
        [l.__dict__ for l in loans],
        ops.__dict__ if ops else None,
    )

    external = await get_all_external_data()

    prediction_data = latest_prediction.__dict__ if latest_prediction else {
        "credit_risk_score": 0.5,
        "repayment_probability": 0.5,
        "debt_capacity": 0,
        "financial_health_risk": "unknown",
        "environmental_risk": "unknown",
        "market_risk": "unknown",
        "overall_financing_risk": "unknown",
        "model_confidence": 0,
    }

    latest_fin = financials[0].__dict__ if financials else {}

    memo_sections = generate_decision_memo(
        farmer.full_name,
        latest_fin,
        [l.__dict__ for l in loans],
        external,
        ratios,
        prediction_data,
        [],
    )

    memo = DecisionMemo(
        farmer_id=farmer_id,
        financial_summary=memo_sections.get("financial_summary"),
        existing_loans_summary=memo_sections.get("existing_loans_summary"),
        external_risks_summary=memo_sections.get("external_risks_summary"),
        financial_ratios_analysis=memo_sections.get("recommendation"),
        ml_prediction_summary=memo_sections.get("recommendation"),
        recommendation=memo_sections.get("recommendation"),
        supporting_evidence=memo_sections.get("supporting_evidence"),
        full_memo=memo_sections.get("full_memo"),
        generated_by="gemini" if memo_sections.get("recommendation", "").startswith("[Gemini") else "rule_based",
        confidence_level="medium",
    )
    db.add(memo)
    db.commit()
    db.refresh(memo)

    return memo


@router.get("/farmers/{farmer_id}/decision-memos", response_model=list[DecisionMemoRead])
def get_decision_memos(farmer_id: int, db: Session = Depends(get_db)):
    return (
        db.query(DecisionMemo)
        .filter(DecisionMemo.farmer_id == farmer_id)
        .order_by(DecisionMemo.created_at.desc())
        .all()
    )


# ---------------------------------------------------------------------------
# Explain Metric (Gemini)
# ---------------------------------------------------------------------------
@router.get("/explain/{metric_name}")
def explain_metric(metric_name: str, value: float, farmer_name: str = "the farmer"):
    """Get a plain-English explanation of a financial metric."""
    explanation = explain_financial_metric(metric_name, value, farmer_name)
    return {"metric": metric_name, "value": value, "explanation": explanation}


# ---------------------------------------------------------------------------
# Unified Farmer Profile
# ---------------------------------------------------------------------------
@router.get("/farmers/{farmer_id}/full-profile", response_model=FullProfile)
async def get_full_profile(farmer_id: int, db: Session = Depends(get_db)):
    """Get the complete unified farmer profile — all data sources merged."""
    farmer = db.get(Farmer, farmer_id)
    if not farmer:
        raise HTTPException(404, "Farmer not found")

    financials = (
        db.query(FinancialRecord)
        .filter(FinancialRecord.farmer_id == farmer_id)
        .order_by(FinancialRecord.year.desc())
        .all()
    )
    loans = (
        db.query(ExistingLoan)
        .filter(ExistingLoan.farmer_id == farmer_id)
        .all()
    )
    ops = (
        db.query(OperationalData)
        .filter(OperationalData.farmer_id == farmer_id)
        .all()
    )
    latest_pred = (
        db.query(Prediction)
        .filter(Prediction.farmer_id == farmer_id)
        .order_by(Prediction.created_at.desc())
        .first()
    )
    scenarios = (
        db.query(ScenarioResult)
        .filter(ScenarioResult.farmer_id == farmer_id)
        .order_by(ScenarioResult.created_at.desc())
        .all()
    )
    latest_memo = (
        db.query(DecisionMemo)
        .filter(DecisionMemo.farmer_id == farmer_id)
        .order_by(DecisionMemo.created_at.desc())
        .first()
    )

    ratios = calculate_financial_ratios(
        [r.__dict__ for r in financials],
        [l.__dict__ for l in loans],
        ops[0].__dict__ if ops else None,
    ) if financials else {}

    external = await get_all_external_data()

    return FullProfile(
        farmer={k: str(v) if hasattr(v, 'isoformat') else v
                for k, v in farmer.__dict__.items() if not k.startswith("_")},
        financial_records=[{k: str(v) if hasattr(v, 'isoformat') else v
                            for k, v in r.__dict__.items() if not k.startswith("_")}
                           for r in financials],
        existing_loans=[{k: str(v) if hasattr(v, 'isoformat') else v
                         for k, v in l.__dict__.items() if not k.startswith("_")}
                        for l in loans],
        operational_data=[{k: str(v) if hasattr(v, 'isoformat') else v
                           for k, v in o.__dict__.items() if not k.startswith("_")}
                          for o in ops],
        external_data=external,
        financial_ratios=ratios,
        latest_prediction={k: str(v) if hasattr(v, 'isoformat') else v
                           for k, v in latest_pred.__dict__.items()
                           if not k.startswith("_")} if latest_pred else None,
        scenarios=[{k: str(v) if hasattr(v, 'isoformat') else v
                    for k, v in s.__dict__.items() if not k.startswith("_")}
                   for s in scenarios],
        latest_memo={k: str(v) if hasattr(v, 'isoformat') else v
                     for k, v in latest_memo.__dict__.items()
                     if not k.startswith("_")} if latest_memo else None,
    )


# ---------------------------------------------------------------------------
# Bank Officer — Applications Overview
# ---------------------------------------------------------------------------
@router.get("/bank/applications")
def get_bank_applications(limit: int = 20, db: Session = Depends(get_db)):
    """Bank officer view: list of farmers with risk status."""
    farmers = db.query(Farmer).order_by(Farmer.id.desc()).limit(limit).all()

    applications = []
    for f in farmers:
        latest_pred = (
            db.query(Prediction)
            .filter(Prediction.farmer_id == f.id)
            .order_by(Prediction.created_at.desc())
            .first()
        )
        ops = (
            db.query(OperationalData)
            .filter(OperationalData.farmer_id == f.id)
            .first()
        )

        risk = latest_pred.overall_financing_risk if latest_pred else "unknown"
        score = latest_pred.credit_risk_score if latest_pred else None

        if risk == "low":
            status = "Ready for Review"
        elif risk == "medium":
            status = "Under Review"
        elif risk == "high":
            status = "Manual Review Required"
        else:
            status = "Pending Assessment"

        applications.append({
            "id": f.id,
            "name": f.full_name,
            "state": f.state,
            "district": f.district,
            "crop": ops.crop_type if ops else "N/A",
            "farm_size_ha": ops.farm_size_acres if ops else 0,
            "risk_level": risk,
            "risk_score": round(score, 2) if score else None,
            "status": status,
            "uc_score": f.cibil_score,
        })

    return {
        "total": db.query(Farmer).count(),
        "applications": applications,
    }


# ---------------------------------------------------------------------------
# Environmental Risk Score
# ---------------------------------------------------------------------------
@router.get("/environmental-score")
async def get_environmental_score():
    """Get composite environmental risk score (0-100)."""
    from ..services.environmental_score import calculate_environmental_score
    from ..services.external_data import get_all_external_data

    external = await get_all_external_data()
    score = calculate_environmental_score(
        external["weather"],
        external["commodity"],
        external["fuel"],
    )
    return score


# ---------------------------------------------------------------------------
# Scenario Comparison (Before vs After)
# ---------------------------------------------------------------------------
@router.get("/farmers/{farmer_id}/scenario-comparison/{scenario_id}")
def get_scenario_comparison(farmer_id: int, scenario_id: int, db: Session = Depends(get_db)):
    """Compare baseline ratios vs scenario outcome."""
    scenario = db.get(ScenarioResult, scenario_id)
    if not scenario or scenario.farmer_id != farmer_id:
        raise HTTPException(404, "Scenario not found")

    # Get current baseline
    latest_pred = (
        db.query(Prediction)
        .filter(Prediction.farmer_id == farmer_id)
        .order_by(Prediction.created_at.desc())
        .first()
    )

    financials = (
        db.query(FinancialRecord)
        .filter(FinancialRecord.farmer_id == farmer_id)
        .order_by(FinancialRecord.year.desc())
        .all()
    )
    loans = (
        db.query(ExistingLoan)
        .filter(ExistingLoan.farmer_id == farmer_id)
        .all()
    )

    current_ratios = calculate_financial_ratios(
        [r.__dict__ for r in financials],
        [l.__dict__ for l in loans],
    ) if financials else {}

    return {
        "scenario_name": scenario.scenario_name,
        "scenario_type": scenario.scenario_type,
        "current": {
            "debt_to_income": current_ratios.get("debt_to_income"),
            "dscr": current_ratios.get("dscr"),
            "credit_risk": latest_pred.credit_risk_score if latest_pred else None,
            "repayment_probability": latest_pred.repayment_probability if latest_pred else None,
            "debt_capacity": latest_pred.debt_capacity if latest_pred else None,
            "overall_risk": latest_pred.overall_financing_risk if latest_pred else "N/A",
        },
        "scenario": {
            "debt_to_income": scenario.new_debt_to_income,
            "dscr": scenario.new_dscr,
            "credit_risk": scenario.new_credit_risk,
            "repayment_probability": scenario.new_repayment_probability,
            "debt_capacity": scenario.new_debt_capacity,
            "overall_risk": scenario.risk_change,
        },
        "risk_change": scenario.risk_change,
        "recommendation": scenario.recommendation,
    }


# ---------------------------------------------------------------------------
# Data Quality & Preprocessing
# ---------------------------------------------------------------------------
@router.get("/farmers/{farmer_id}/data-quality")
def get_data_quality_report(farmer_id: int, db: Session = Depends(get_db)):
    """Run the full preprocessing pipeline and return a data quality report."""
    from ..services.preprocessing import run_full_preprocessing

    financials = (
        db.query(FinancialRecord)
        .filter(FinancialRecord.farmer_id == farmer_id)
        .order_by(FinancialRecord.year.desc())
        .all()
    )
    loans = (
        db.query(ExistingLoan)
        .filter(ExistingLoan.farmer_id == farmer_id)
        .all()
    )
    ops = (
        db.query(OperationalData)
        .filter(OperationalData.farmer_id == farmer_id)
        .first()
    )

    if not financials:
        raise HTTPException(404, "No financial records found")

    report = run_full_preprocessing(
        farmer_id,
        [r.__dict__ for r in financials],
        [l.__dict__ for l in loans],
        ops.__dict__ if ops else None,
    )
    return report


@router.get("/data-quality/overview")
def get_data_quality_overview(limit: int = 100, db: Session = Depends(get_db)):
    """Aggregated data quality overview across all farmers."""
    from ..services.preprocessing import run_full_preprocessing

    farmers = db.query(Farmer).order_by(Farmer.id.desc()).limit(limit).all()

    total_issues = 0
    total_outliers = 0
    total_duplicates = 0
    total_missing = 0
    quality_scores = []

    for f in farmers:
        financials = (
            db.query(FinancialRecord)
            .filter(FinancialRecord.farmer_id == f.id)
            .order_by(FinancialRecord.year.desc())
            .all()
        )
        if not financials:
            continue
        loans = (
            db.query(ExistingLoan)
            .filter(ExistingLoan.farmer_id == f.id)
            .all()
        )
        ops = (
            db.query(OperationalData)
            .filter(OperationalData.farmer_id == f.id)
            .first()
        )

        report = run_full_preprocessing(
            f.id,
            [r.__dict__ for r in financials],
            [l.__dict__ for l in loans],
            ops.__dict__ if ops else None,
        )
        s = report["summary"]
        total_issues += s["validation_errors"] + s["missing_values"] + s["duplicates"]
        total_outliers += s["outliers"]
        total_duplicates += s["duplicates"]
        total_missing += s["missing_values"]
        quality_scores.append(s["data_quality_score"])

    n = len(quality_scores)
    return {
        "farmers_analyzed": n,
        "total_validation_issues": total_issues,
        "total_outliers": total_outliers,
        "total_duplicates": total_duplicates,
        "total_missing_values": total_missing,
        "average_quality_score": round(sum(quality_scores) / max(n, 1), 1) if n > 0 else 0,
        "quality_distribution": {
            "excellent_90plus": sum(1 for s in quality_scores if s >= 90),
            "good_70_89": sum(1 for s in quality_scores if 70 <= s < 90),
            "fair_50_69": sum(1 for s in quality_scores if 50 <= s < 70),
            "poor_below_50": sum(1 for s in quality_scores if s < 50),
        },
    }


# ---------------------------------------------------------------------------
# ML Evaluation
# ---------------------------------------------------------------------------
@router.get("/ml/evaluation")
def get_ml_evaluation():
    """Get the latest ML model evaluation metrics."""
    from ..services.feature_engineering import get_latest_evaluation

    eval_data = get_latest_evaluation()
    if not eval_data:
        raise HTTPException(404, "No evaluation data found. Run training first.")

    return eval_data


@router.post("/ml/retrain")
def retrain_models(db: Session = Depends(get_db)):
    """Retrain ML models with full pipeline (CV, grid search, evaluation)."""
    from ..services.ml_service import _train_from_database, _fit_and_save_models

    farmer_count = db.query(Farmer).count()
    if farmer_count < 10:
        raise HTTPException(400, f"Need at least 10 farmers, found {farmer_count}")

    logger.info(f"Retraining models on {farmer_count} farmers with full pipeline...")
    risk_model, repay_model, cap_model = _train_from_database(db, farmer_count, use_full_pipeline=True)

    return {
        "status": "retrained",
        "farmers_used": farmer_count,
        "message": "Models retrained with cross-validation, grid search, and full evaluation",
    }
