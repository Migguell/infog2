from pydantic import BaseModel, Field, ConfigDict, HttpUrl
from typing import Optional, List
from datetime import datetime
import uuid
from decimal import Decimal
from app.product_image.schemas import ProductImageResponse

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Nome do produto.")
    description: str = Field(..., min_length=1, description="Descrição detalhada do produto.")
    price: Decimal = Field(..., gt=0, decimal_places=2, description="Preço do produto.")
    inventory: int = Field(..., ge=0, description="Quantidade em estoque do produto.")
    size_id: int = Field(description="ID do tamanho do produto (referencia Size.id).")
    category_id: int = Field(description="ID da categoria do produto (referencia Category.id).")
    gender_id: int = Field(description="ID do gênero do produto (referencia Gender.id).")
    product_image_ids: Optional[List[uuid.UUID]] = Field(None, description="Lista de IDs de imagens de produto (ProductImage.id) a serem associadas a este produto.")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "name": "Camiseta Algodão Pima Premium",
                "description": "Camiseta de alta qualidade, confeccionada com algodão Pima peruano, proporcionando maciez e durabilidade excepcionais. Modelagem clássica.",
                "price": "129.90",
                "inventory": 150,
                "size_id": 2,
                "category_id": 1,
                "gender_id": 1,
                "product_image_ids": [
                    "00112233-4455-6677-8899-aabbccddeeff",
                    "11223344-5566-7788-99aa-bbccddeeff00"
                ]
            }
        }
    )


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Novo nome do produto.")
    description: Optional[str] = Field(None, min_length=1, description="Nova descrição do produto.")
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2, description="Novo preço do produto.")
    inventory: Optional[int] = Field(None, ge=0, description="Nova quantidade em estoque.")
    size_id: Optional[int] = Field(None, description="Novo ID de tamanho.")
    category_id: Optional[int] = Field(None, description="Novo ID de categoria.")
    gender_id: Optional[int] = Field(None, description="Novo ID de gênero.")
    product_image_ids: Optional[List[uuid.UUID]] = Field(None, description="Nova lista de IDs de imagens de produto para associar.")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "price": "135.50",
                "inventory": 120,
                "product_image_ids": ["00112233-4455-6677-8899-aabbccddeeff"]
            }
        }
    )

class ProductResponse(BaseModel):
    id: uuid.UUID = Field(description="ID único do produto.")
    name: str = Field(description="Nome do produto.")
    description: str = Field(description="Descrição do produto.")
    price: Decimal = Field(description="Preço do produto.")
    inventory: int = Field(description="Quantidade em estoque.")
    size_id: int = Field(description="ID do tamanho associado.")
    category_id: int = Field(description="ID da categoria associada.")
    gender_id: int = Field(description="ID do gênero associado.")
    created_at: datetime = Field(description="Data e hora de criação do produto.")
    updated_at: datetime = Field(description="Data e hora da última atualização do produto.")
    images: List[ProductImageResponse] = Field([], description="Lista de imagens associadas ao produto.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "name": "Camiseta Algodão Pima Premium",
                "description": "Camiseta de alta qualidade, confeccionada com algodão Pima peruano...",
                "price": "129.90",
                "inventory": 150,
                "size_id": 2,
                "category_id": 1,
                "gender_id": 1,
                "created_at": "2024-05-25T12:00:00Z",
                "updated_at": "2024-05-25T12:10:00Z",
                "images": [
                    {
                        "id": "00112233-4455-6677-8899-aabbccddeeff",
                        "product_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                        "url": "http://example.com/images/produto_frente.jpg",
                        "description": "Vista frontal da camiseta",
                        "is_main": True,
                        "created_at": "2024-05-25T11:00:00Z",
                        "updated_at": "2024-05-25T11:05:00Z"
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