"""Scenario Pydantic schemas."""
from datetime import datetime
from pydantic import BaseModel, Field


class ScenarioRequest(BaseModel):
    farmer_id: int
    scenario_type: str = Field(
        ..., description="rainfall, commodity, new_loan, interest, fuel, tractor_purchase"
    )
    parameters: dict = Field(
        ..., description="Scenario-specific parameters (e.g., {'rainfall_change_pct': -20})"
    )


class ScenarioResultRead(BaseModel):
    id: int
    farmer_id: int
    scenario_name: str
    scenario_type: str
    parameters_json: str
    new_debt_to_income: float | None
    new_dscr: float | None
    new_credit_risk: float | None
    new_repayment_probability: float | None
    new_debt_capacity: float | None
    risk_change: str | None
    recommendation: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
