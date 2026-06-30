"""
DecisionMemo model — stores AI-generated decision memos.
"""
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class DecisionMemo(Base):
    __tablename__ = "decision_memos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    farmer_id: Mapped[int] = mapped_column(
        ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False
    )

    # Memo sections (Gemini-generated content)
    financial_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    existing_loans_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_risks_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    financial_ratios_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    ml_prediction_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    scenario_analysis_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    supporting_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Full memo text (combined)
    full_memo: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metadata
    generated_by: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # gemini or rule_based
    confidence_level: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # high, medium, low

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationship
    farmer: Mapped["Farmer"] = relationship(
        "Farmer", back_populates="decision_memos"
    )

    def __repr__(self) -> str:
        return f"<DecisionMemo(id={self.id}, farmer_id={self.farmer_id})>"
