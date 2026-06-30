"""FinancialRecord Pydantic schemas."""
from datetime import datetime
from pydantic import BaseModel


class FinancialRecordCreate(BaseModel):
    farmer_id: int
    year: int
    revenue: float = 0.0
    operating_expenses: float = 0.0
    interest_expense: float = 0.0
    depreciation: float = 0.0
    net_income: float = 0.0
    total_assets: float = 0.0
    current_assets: float = 0.0
    fixed_assets: float = 0.0
    total_liabilities: float = 0.0
    current_liabilities: float = 0.0
    long_term_debt: float = 0.0
    equity: float = 0.0
    operating_cash_flow: float = 0.0
    free_cash_flow: float = 0.0
    source_document: str | None = None


class FinancialRecordRead(BaseModel):
    id: int
    farmer_id: int
    year: int
    revenue: float
    operating_expenses: float
    interest_expense: float
    depreciation: float
    net_income: float
    total_assets: float
    current_assets: float
    fixed_assets: float
    total_liabilities: float
    current_liabilities: float
    long_term_debt: float
    equity: float
    operating_cash_flow: float
    free_cash_flow: float
    source_document: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
