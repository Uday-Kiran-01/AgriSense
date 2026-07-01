"""
ScenarioResult model - stores "what-if" scenario analysis results.
"""
from datetime import datetime

from sqlalchemy import String, Float, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class ScenarioResult(Base):
    __tablename__ = "scenario_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    farmer_id: Mapped[int] = mapped_column(
        ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False
    )

    scenario_name: Mapped[str] = mapped_column(String(200), nullable=False)
    scenario_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # rainfall, commodity, new_loan, interest, fuel

    # Scenario parameters (JSON)
    parameters_json: Mapped[str] = mapped_column(Text, nullable=False)

    # Recalculated metrics
    new_debt_to_income: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_dscr: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_credit_risk: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_repayment_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_debt_capacity: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Impact assessment
    risk_change: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # improved, worsened, unchanged
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<ScenarioResult(id={self.id}, name='{self.scenario_name}')>"
