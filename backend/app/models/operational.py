"""
OperationalData model — farm-specific operational information.
"""
from datetime import datetime

from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class OperationalData(Base):
    __tablename__ = "operational_data"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    farmer_id: Mapped[int] = mapped_column(
        ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False
    )

    season: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # kharif, rabi, zaid, annual

    # Farm details
    farm_size_acres: Mapped[float] = mapped_column(Float, nullable=False)
    land_ownership: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # owned, leased, mixed
    land_value_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Crop details
    crop_type: Mapped[str] = mapped_column(String(100), nullable=False)
    crop_yield_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_price_per_kg: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Machinery and equipment
    machinery_value: Mapped[float | None] = mapped_column(Float, nullable=True, default=0.0)
    has_tractor: Mapped[bool] = mapped_column(default=False)
    has_irrigation: Mapped[bool] = mapped_column(default=False)
    has_insurance: Mapped[bool] = mapped_column(default=False)

    # Production
    annual_production_kg: Mapped[float | None] = mapped_column(Float, nullable=True)

    source_document: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationship
    farmer: Mapped["Farmer"] = relationship(
        "Farmer", back_populates="operational_data"
    )

    @property
    def revenue_per_acre(self) -> float | None:
        """Calculate revenue per acre."""
        if self.expected_price_per_kg and self.crop_yield_kg and self.farm_size_acres:
            return (self.crop_yield_kg * self.expected_price_per_kg) / max(
                self.farm_size_acres, 1
            )
        return None

    def __repr__(self) -> str:
        return f"<OperationalData(id={self.id}, crop='{self.crop_type}', acres={self.farm_size_acres})>"
