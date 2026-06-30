"""
FinancialRecord model — stores extracted financial data per year.
"""
from datetime import datetime

from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class FinancialRecord(Base):
    __tablename__ = "financial_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    farmer_id: Mapped[int] = mapped_column(
        ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False
    )

    year: Mapped[int] = mapped_column(Integer, nullable=False)  # financial year

    # Income Statement
    revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    operating_expenses: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    interest_expense: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    depreciation: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    net_income: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Balance Sheet
    total_assets: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    current_assets: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fixed_assets: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_liabilities: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    current_liabilities: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    long_term_debt: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    equity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Cash Flow
    operating_cash_flow: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    free_cash_flow: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Data provenance
    source_document: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )  # which document this data came from

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationship
    farmer: Mapped["Farmer"] = relationship(
        "Farmer", back_populates="financial_records"
    )

    def __repr__(self) -> str:
        return f"<FinancialRecord(id={self.id}, year={self.year}, revenue={self.revenue})>"
