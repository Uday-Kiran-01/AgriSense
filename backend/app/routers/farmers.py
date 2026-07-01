"""
AgriSense API Router - all endpoints for the platform.
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
from ..services.scenario_analysis import run_single_scenario, _generate_investment_narrative
from ..services.gemini_service import generate_decision_memo, explain_financial_metric
from ..services.external_data import get_all_external_data
from ..logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["Farmers"])


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
