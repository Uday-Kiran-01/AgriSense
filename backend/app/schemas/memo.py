"""DecisionMemo and FullProfile Pydantic schemas."""
from datetime import datetime
from pydantic import BaseModel


class DecisionMemoRead(BaseModel):
    id: int
    farmer_id: int
    financial_summary: str | None
    existing_loans_summary: str | None
    external_risks_summary: str | None
    financial_ratios_analysis: str | None
    ml_prediction_summary: str | None
    scenario_analysis_summary: str | None
    recommendation: str | None
    supporting_evidence: str | None
    full_memo: str | None
    generated_by: str | None
    confidence_level: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class FullProfile(BaseModel):
    """Unified farmer profile combining all data sources."""
    farmer: dict
    financial_records: list[dict]
    existing_loans: list[dict]
    operational_data: list[dict]
    external_data: dict  # weather, commodity, government
    financial_ratios: dict  # calculated ratios
    latest_prediction: dict | None
    scenarios: list[dict]
    latest_memo: dict | None
