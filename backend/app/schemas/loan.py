"""ExistingLoan Pydantic schemas."""
from datetime import datetime
from pydantic import BaseModel, Field


class LoanCreate(BaseModel):
    farmer_id: int
    loan_type: str = Field(
        ..., description="farm_loan, tractor_loan, equipment_loan, mortgage, credit_line"
    )
    lender: str | None = None
    original_amount: float
    outstanding_balance: float
    monthly_emi: float
    interest_rate: float  # annual %
    start_date: datetime | None = None
    end_date: datetime | None = None
    months_remaining: int | None = None
    on_time_payments: int = 0
    total_payments_due: int = 0


class LoanRead(BaseModel):
    id: int
    farmer_id: int
    loan_type: str
    lender: str | None
    original_amount: float
    outstanding_balance: float
    monthly_emi: float
    interest_rate: float
    start_date: datetime | None
    end_date: datetime | None
    months_remaining: int | None
    on_time_payments: int
    total_payments_due: int
    annual_debt_service: float
    repayment_ratio: float
    created_at: datetime

    model_config = {"from_attributes": True}
