"""
Document model - stores uploaded document metadata.
"""
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    farmer_id: Mapped[int] = mapped_column(
        ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False
    )

    # Document metadata
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    document_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # financial_statement, loan_doc, farm_doc, bank_statement, tax_return, insurance, land_record
    sub_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # e.g., "balance_sheet", "income_statement", "farm_loan_agreement"

    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Extraction provenance tracking
    extracted_data: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON string of extracted values

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationship
    farmer: Mapped["Farmer"] = relationship("Farmer", back_populates="documents")

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, type='{self.document_type}', file='{self.filename}')>"
