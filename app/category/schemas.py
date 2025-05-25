from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Nome da categoria a ser criada.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Camisetas"
            }
        }
    )

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="Novo nome para a categoria (opcional).")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Camisetas Manga Longa"
            }
        }
    )

class CategoryResponse(BaseModel):
    id: int = Field(description="ID único da categoria.")
    name: str = Field(description="Nome da categoria.")
    created_at: datetime = Field(description="Data e hora de criação da categoria.")
    updated_at: datetime = Field(description="Data e hora da última atualização da categoria.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Camisetas",
                "created_at": "2024-05-24T12:00:00Z",
                "updated_at": "2024-05-24T12:05:00Z"
            }
        }
    )

class MessageResponse(BaseModel):
    message: str = Field(description="Mensagem de resposta da operação.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Operação realizada com sucesso."
            }
        }
    )