"""
ExternalData model - stores weather, commodity, and government data.
"""
from datetime import datetime, date

from sqlalchemy import String, Float, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class ExternalData(Base):
    __tablename__ = "external_data"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    data_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # weather, commodity, government

    # Common fields
    data_date: Mapped[date] = mapped_column(Date, nullable=False)
    region: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )  # for weather region

    # Weather fields
    rainfall_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature_celsius: Mapped[float | None] = mapped_column(Float, nullable=True)
    drought_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    flood_risk: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # low, medium, high

    # Commodity fields
    commodity_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    commodity_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    price_change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Fuel / input costs
    fuel_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    fertilizer_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Government
    subsidy_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    subsidy_amount: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Metadata
    source: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # openweathermap, alphavantage, mock
    is_mock: Mapped[bool] = mapped_column(default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<ExternalData(id={self.id}, type='{self.data_type}', date={self.data_date})>"
