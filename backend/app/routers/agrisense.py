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
# Scenario Analysis
# ---------------------------------------------------------------------------
@router.post("/scenarios", response_model=ScenarioResultRead)
async def run_scenario_analysis(req: ScenarioRequest, db: Session = Depends(get_db)):
    """Run a what-if scenario."""
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

    result = run_scenario(
        req.scenario_type,
        req.parameters,
        [r.__dict__ for r in financials],
        [l.__dict__ for l in loans],
        ops.__dict__ if ops else None,
        base_ratios,
    )

    # Store result
    scenario = ScenarioResult(
        farmer_id=req.farmer_id,
        scenario_name=result["scenario_name"],
        scenario_type=result["scenario_type"],
        parameters_json=json.dumps(result["parameters"]),
        new_debt_to_income=result["new_ratios"].get("debt_to_income"),
        new_dscr=result["new_ratios"].get("dscr"),
        new_credit_risk=None,
        new_repayment_probability=None,
        new_debt_capacity=None,
        risk_change=result["risk_change"],
        recommendation=result.get("recommendation"),
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)

    return scenario


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
