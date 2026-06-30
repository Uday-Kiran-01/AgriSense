"""Prediction Pydantic schemas."""
from datetime import datetime
from pydantic import BaseModel


class RiskBreakdown(BaseModel):
    financial_health_risk: str  # low, medium, high
    environmental_risk: str
    market_risk: str
    overall_financing_risk: str


class PredictionRead(BaseModel):
    id: int
    farmer_id: int
    credit_risk_score: float
    repayment_probability: float
    debt_capacity: float
    model_confidence: float | None
    model_version: str | None
    feature_importance_json: str | None
    financial_health_risk: str | None
    environmental_risk: str | None
    market_risk: str | None
    overall_financing_risk: str | None
    input_features_json: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
