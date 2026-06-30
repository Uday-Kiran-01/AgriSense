"""Farmer Pydantic schemas."""
from datetime import datetime
from pydantic import BaseModel, Field


class FarmerCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    state: str | None = None
    district: str | None = None
    cibil_score: int | None = None
    years_in_farming: int | None = None


class FarmerUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    state: str | None = None
    district: str | None = None
    cibil_score: int | None = None
    years_in_farming: int | None = None


class FarmerRead(BaseModel):
    id: int
    full_name: str
    email: str | None
    phone: str | None
    address: str | None
    state: str | None
    district: str | None
    cibil_score: int | None
    years_in_farming: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
