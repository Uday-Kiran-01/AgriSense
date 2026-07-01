"""
ExistingLoan model - tracks all existing financing for a farmer.
"""
from datetime import datetime

from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class ExistingLoan(Base):
    __tablename__ = "existing_loans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    farmer_id: Mapped[int] = mapped_column(
        ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False
    )

    loan_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # farm_loan, tractor_loan, equipment_loan, mortgage, credit_line
    lender: Mapped[str] = mapped_column(String(200), nullable=True)
    original_amount: Mapped[float] = mapped_column(Float, nullable=False)
    outstanding_balance: Mapped[float] = mapped_column(Float, nullable=False)
    monthly_emi: Mapped[float] = mapped_column(Float, nullable=False)
    interest_rate: Mapped[float] = mapped_column(Float, nullable=False)  # annual %
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    months_remaining: Mapped[int] = mapped_column(Integer, nullable=True)

    # Repayment history (for credit assessment)
    on_time_payments: Mapped[int] = mapped_column(Integer, default=0)
    total_payments_due: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationship
    farmer: Mapped["Farmer"] = relationship("Farmer", back_populates="existing_loans")

    @property
    def annual_debt_service(self) -> float:
        """Yearly debt obligation for this loan."""
        return self.monthly_emi * 12

    @property
    def repayment_ratio(self) -> float:
        """Ratio of on-time payments to total payments due."""
        if self.total_payments_due == 0:
            return 1.0
        return self.on_time_payments / self.total_payments_due

    def __repr__(self) -> str:
        return f"<ExistingLoan(id={self.id}, type='{self.loan_type}', balance={self.outstanding_balance})>"
