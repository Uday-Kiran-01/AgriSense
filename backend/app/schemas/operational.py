"""OperationalData Pydantic schemas."""
from datetime import datetime
from pydantic import BaseModel, Field


class OperationalDataCreate(BaseModel):
    farmer_id: int
    season: str = Field(..., description="kharif, rabi, zaid, annual")
    farm_size_acres: float
    land_ownership: str = Field(..., description="owned, leased, mixed")
    land_value_estimate: float | None = None
    crop_type: str
    crop_yield_kg: float | None = None
    expected_price_per_kg: float | None = None
    machinery_value: float | None = 0.0
    has_tractor: bool = False
    has_irrigation: bool = False
    has_insurance: bool = False
    annual_production_kg: float | None = None
    source_document: str | None = None


class OperationalDataRead(BaseModel):
    id: int
    farmer_id: int
    season: str
    farm_size_acres: float
    land_ownership: str
    land_value_estimate: float | None
    crop_type: str
    crop_yield_kg: float | None
    expected_price_per_kg: float | None
    machinery_value: float | None
    has_tractor: bool
    has_irrigation: bool
    has_insurance: bool
    annual_production_kg: float | None
    revenue_per_acre: float | None
    source_document: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
