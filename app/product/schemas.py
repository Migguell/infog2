from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid
from decimal import Decimal

class ProductImageCreate(BaseModel):
    url: str = Field(..., max_length=500)
    description: Optional[str] = Field(None, max_length=255)
    is_main: bool = False

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

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    price: Decimal = Field(..., gt=0, decimal_places=2)
    inventory: int = Field(..., ge=0)
    size_id: int
    category_id: int
    gender_id: int
    images: Optional[List[ProductImageCreate]] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    inventory: Optional[int] = Field(None, ge=0)
    size_id: Optional[int] = None
    category_id: Optional[int] = None
    gender_id: Optional[int] = None
    images: Optional[List[ProductImageCreate]] = None

class ProductResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    price: Decimal
    inventory: int
    size_id: int
    category_id: int
    gender_id: int
    created_at: datetime
    updated_at: datetime
    images: List[ProductImageResponse] = []

    class Config:
        from_attributes = True

