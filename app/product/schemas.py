from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
import uuid
from decimal import Decimal
from app.product_image.schemas import ProductImageResponse # <--- Importado de product_image.schemas

# ProductImageCreate e ProductImageResponse NÃO SÃO MAIS DEFINIDOS AQUI.
# Eles devem estar no arquivo app/product_image/schemas.py.

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    price: Decimal = Field(..., gt=0, decimal_places=2)
    inventory: int = Field(..., ge=0)
    size_id: int
    category_id: int
    gender_id: int
    product_image_ids: Optional[List[uuid.UUID]] = None # <--- Alterado para lista de IDs de imagens

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    inventory: Optional[int] = Field(None, ge=0)
    size_id: Optional[int] = None
    category_id: Optional[int] = None
    gender_id: Optional[int] = None
    product_image_ids: Optional[List[uuid.UUID]] = None # <--- Alterado para lista de IDs de imagens

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
    images: List[ProductImageResponse] = [] # <--- Tipo continua sendo ProductImageResponse

    # APENAS model_config DEVE EXISTIR. A CLASSE 'Config' FOI REMOVIDA para evitar o erro.
    model_config = ConfigDict(from_attributes=True)

class MessageResponse(BaseModel):
    message: str
