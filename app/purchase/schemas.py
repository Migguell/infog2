from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
import uuid
from decimal import Decimal

class PurchaseItemCreate(BaseModel):
    product_id: uuid.UUID = Field(description="ID do produto a ser incluído no pedido.")
    size_id: int = Field(description="ID do tamanho do produto selecionado.")
    quantity: int = Field(..., gt=0, description="Quantidade do produto.")
    unit_price_at_purchase: Decimal = Field(..., gt=0, decimal_places=2, description="Preço unitário do produto no momento da compra.")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "product_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "size_id": 2,
                "quantity": 1,
                "unit_price_at_purchase": "129.90"
            }
        }
    )

class PurchaseItemResponse(BaseModel):
    id: uuid.UUID = Field(description="ID único do item do pedido.")
    purchase_id: uuid.UUID = Field(description="ID do pedido ao qual este item pertence.")
    product_id: uuid.UUID = Field(description="ID do produto.")
    size_id: int = Field(description="ID do tamanho.")
    quantity: int = Field(description="Quantidade comprada.")
    unit_price_at_purchase: Decimal = Field(description="Preço unitário no momento da compra.")
    total_price: Decimal = Field(description="Preço total para este item.")
    created_at: datetime = Field(description="Data de criação do item do pedido.")
    updated_at: datetime = Field(description="Data de atualização do item do pedido.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra = {
            "example": {
                "id": "c1d2e3f4-a5b6-c7d8-e9f0-a1b2c3d4e5f6",
                "purchase_id": "f1e2d3c4-b5a6-9876-5432-fedcba987654",
                "product_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "size_id": 2,
                "quantity": 1,
                "unit_price_at_purchase": "129.90",
                "total_price": "129.90",
                "created_at": "2024-05-25T15:00:00Z",
                "updated_at": "2024-05-25T15:00:00Z"
            }
        }
    )

class PurchaseCreate(BaseModel):
    client_id: uuid.UUID = Field(description="ID do cliente que está realizando o pedido.")
    items: List[PurchaseItemCreate] = Field(..., min_length=1, description="Lista de itens do pedido.")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "client_id": "123e4567-e89b-12d3-a456-426614174000",
                "items": [
                    {
                        "product_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                        "size_id": 2,
                        "quantity": 1,
                        "unit_price_at_purchase": "129.90"
                    },
                    {
                        "product_id": "b2c3d4e5-f6a7-8901-2345-678901bcdef0",
                        "size_id": 3,
                        "quantity": 2,
                        "unit_price_at_purchase": "89.50"
                    }
                ]
            }
        }
    )

class PurchaseUpdate(BaseModel):
    status: Optional[str] = Field(None, max_length=50, description="Novo status do pedido.")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "status": "shipped"
            }
        }
    )

class PurchaseResponse(BaseModel):
    id: uuid.UUID = Field(description="ID único do pedido.")
    client_id: uuid.UUID = Field(description="ID do cliente que fez o pedido.")
    status: str = Field(description="Status atual do pedido.")
    subtotal: Decimal = Field(description="Subtotal do pedido.")
    created_at: datetime = Field(description="Data e hora de criação do pedido.")
    updated_at: datetime = Field(description="Data e hora da última atualização do pedido.")
    items: List[PurchaseItemResponse] = Field([], description="Lista de itens incluídos no pedido.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra = {
            "example": {
                "id": "f1e2d3c4-b5a6-9876-5432-fedcba987654",
                "client_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "pending",
                "subtotal": "308.90",
                "created_at": "2024-05-25T15:00:00Z",
                "updated_at": "2024-05-25T15:00:00Z",
                "items": [
                    {
                        "id": "c1d2e3f4-a5b6-c7d8-e9f0-a1b2c3d4e5f6",
                        "purchase_id": "f1e2d3c4-b5a6-9876-5432-fedcba987654",
                        "product_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                        "size_id": 2,
                        "quantity": 1,
                        "unit_price_at_purchase": "129.90",
                        "total_price": "129.90",
                        "created_at": "2024-05-25T15:00:00Z",
                        "updated_at": "2024-05-25T15:00:00Z"
                    }
                ]
            }
        }
    )

class MessageResponse(BaseModel):
    message: str = Field(description="Mensagem de resposta da operação.")
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "message": "Operação realizada com sucesso."
            }
        }
    )