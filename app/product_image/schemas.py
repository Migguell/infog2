from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class ProductImageCreate(BaseModel):
    product_id: uuid.UUID
    url: str = Field(..., max_length=500)
    description: Optional[str] = Field(None, max_length=255)
    is_main: bool = False

class ProductImageUpdate(BaseModel):
    url: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=255)
    is_main: Optional[bool] = None

class ProductImageResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    url: str
    description: Optional[str]
    is_main: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

