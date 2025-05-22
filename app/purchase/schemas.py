from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid
from decimal import Decimal

class PurchaseItemCreate(BaseModel):
    product_id: uuid.UUID
    size_id: int
    quantity: int = Field(..., gt=0)
    unit_price_at_purchase: Decimal = Field(..., gt=0, decimal_places=2)

class PurchaseItemResponse(BaseModel):
    id: uuid.UUID
    purchase_id: uuid.UUID
    product_id: uuid.UUID
    size_id: int
    quantity: int
    unit_price_at_purchase: Decimal
    total_price: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PurchaseCreate(BaseModel):
    client_id: uuid.UUID
    items: List[PurchaseItemCreate] = Field(..., min_length=1)

class PurchaseUpdate(BaseModel):
    status: Optional[str] = Field(None, max_length=50)

class PurchaseResponse(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    status: str
    subtotal: Decimal
    created_at: datetime
    updated_at: datetime
    items: List[PurchaseItemResponse] = []

    class Config:
        from_attributes = True

