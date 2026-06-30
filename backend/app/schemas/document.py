"""Document Pydantic schemas."""
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    farmer_id: int
    filename: str
    document_type: str = Field(
        ...,
        description="financial_statement, loan_doc, farm_doc, bank_statement, tax_return, insurance, land_record",
    )
    sub_type: str | None = None
    file_path: str
    description: str | None = None
    extracted_data: str | None = None


class DocumentRead(BaseModel):
    id: int
    farmer_id: int
    filename: str
    document_type: str
    sub_type: str | None
    file_path: str
    description: str | None
    extracted_data: str | None
    uploaded_at: datetime

    model_config = {"from_attributes": True}
