"""
Farmer model - the core entity in AgriSense.
"""
from datetime import datetime

from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Farmer(Base):
    __tablename__ = "farmers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    state: Mapped[str] = mapped_column(String(100), nullable=True)
    district: Mapped[str] = mapped_column(String(100), nullable=True)

    # Credit profile (mock for demo)
    cibil_score: Mapped[int | None] = mapped_column(nullable=True, default=None)
    years_in_farming: Mapped[int | None] = mapped_column(nullable=True, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="farmer", cascade="all, delete-orphan"
    )
    existing_loans: Mapped[list["ExistingLoan"]] = relationship(
        "ExistingLoan", back_populates="farmer", cascade="all, delete-orphan"
    )
    financial_records: Mapped[list["FinancialRecord"]] = relationship(
        "FinancialRecord", back_populates="farmer", cascade="all, delete-orphan"
    )
    operational_data: Mapped[list["OperationalData"]] = relationship(
        "OperationalData", back_populates="farmer", cascade="all, delete-orphan"
    )
    predictions: Mapped[list["Prediction"]] = relationship(
        "Prediction", back_populates="farmer", cascade="all, delete-orphan"
    )
    decision_memos: Mapped[list["DecisionMemo"]] = relationship(
        "DecisionMemo", back_populates="farmer", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Farmer(id={self.id}, name='{self.full_name}')>"
