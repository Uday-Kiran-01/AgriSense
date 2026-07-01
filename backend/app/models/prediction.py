"""
Prediction model - stores ML model predictions for each farmer.
"""
from datetime import datetime

from sqlalchemy import String, Float, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    farmer_id: Mapped[int] = mapped_column(
        ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False
    )

    # Model predictions
    credit_risk_score: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # 0 (low risk) to 1 (high risk)
    repayment_probability: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # 0 to 1
    debt_capacity: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # max additional loan amount

    # Confidence
    model_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Feature importance (JSON string)
    feature_importance_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Risk breakdown
    financial_health_risk: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # low, medium, high
    environmental_risk: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    market_risk: Mapped[str | None] = mapped_column(String(20), nullable=True)
    overall_financing_risk: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )

    # Input features used (JSON string for audit)
    input_features_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationship
    farmer: Mapped["Farmer"] = relationship("Farmer", back_populates="predictions")

    def __repr__(self) -> str:
        return (
            f"<Prediction(id={self.id}, farmer_id={self.farmer_id}, "
            f"risk={self.credit_risk_score:.2f})>"
        )
