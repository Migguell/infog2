from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class SizeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=20, description="Nome curto do tamanho (ex: 'P', 'M', 'GG').")
    long_name: Optional[str] = Field(None, max_length=35, description="Nome descritivo do tamanho (ex: 'Pequeno', 'Médio', 'Extra Grande').")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "name": "G",
                "long_name": "Grande"
            }
        }
    )

class SizeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=20, description="Novo nome curto do tamanho.")
    long_name: Optional[str] = Field(None, max_length=35, description="Novo nome descritivo do tamanho.")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "name": "XG",
                "long_name": "Extra Grande Especial"
            }
        }
    )

class SizeResponse(BaseModel):
    id: int = Field(description="ID único do tamanho.")
    name: str = Field(description="Nome curto do tamanho.")
    long_name: Optional[str] = Field(description="Nome descritivo do tamanho.")
    created_at: datetime = Field(description="Data e hora de criação do tamanho.")
    updated_at: datetime = Field(description="Data e hora da última atualização do tamanho.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "M",
                "long_name": "Médio",
                "created_at": "2024-05-25T09:00:00Z",
                "updated_at": "2024-05-25T09:00:00Z"
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