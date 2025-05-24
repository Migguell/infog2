from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from typing import Optional
from datetime import datetime
import uuid

class ProductImageCreate(BaseModel):
    product_id: uuid.UUID = Field(description="ID do produto ao qual esta imagem pertence.")
    url: HttpUrl = Field(..., max_length=500, description="URL da imagem.")
    description: Optional[str] = Field(None, max_length=255, description="Descrição opcional da imagem.")
    is_main: bool = Field(False, description="Indica se esta é a imagem principal do produto.")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "product_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "url": "http://example.com/images/produto_frente.jpg",
                "description": "Vista frontal da camiseta",
                "is_main": True
            }
        }
    )

class ProductImageUpdate(BaseModel):
    url: Optional[HttpUrl] = Field(None, max_length=500, description="Nova URL da imagem.")
    description: Optional[str] = Field(None, max_length=255, description="Nova descrição da imagem.")
    is_main: Optional[bool] = Field(None, description="Definir se esta é a imagem principal.")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "description": "Detalhe da estampa da camiseta",
                "is_main": False
            }
        }
    )

class ProductImageResponse(BaseModel):
    id: uuid.UUID = Field(description="ID único da imagem do produto.")
    product_id: uuid.UUID = Field(description="ID do produto associado.")
    url: str = Field(description="URL da imagem.")
    description: Optional[str] = Field(description="Descrição da imagem.")
    is_main: bool = Field(description="Se é a imagem principal do produto.")
    created_at: datetime = Field(description="Data e hora de criação da imagem.")
    updated_at: datetime = Field(description="Data e hora da última atualização da imagem.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra = {
            "example": {
                "id": "00112233-4455-6677-8899-aabbccddeeff",
                "product_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "url": "http://example.com/images/produto_frente.jpg",
                "description": "Vista frontal da camiseta",
                "is_main": True,
                "created_at": "2024-05-25T11:00:00Z",
                "updated_at": "2024-05-25T11:05:00Z"
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