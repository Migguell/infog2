from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class GenderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=20, description="Nome curto do gênero (ex: 'M', 'F', 'U').")
    long_name: Optional[str] = Field(None, max_length=50, description="Nome descritivo do gênero (ex: 'Masculino', 'Feminino', 'Unissex').")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "M",
                "long_name": "Masculino"
            }
        }

class GenderUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=20, description="Novo nome curto do gênero.")
    long_name: Optional[str] = Field(None, max_length=50, description="Novo nome descritivo do gênero.")

    class Config:
        json_schema_extra = {
            "example": {
                "long_name": "Masculino Adulto"
            }
        }

class GenderResponse(BaseModel):
    id: int = Field(description="ID único do gênero.")
    name: str = Field(description="Nome curto do gênero.")
    long_name: Optional[str] = Field(description="Nome descritivo do gênero.")
    created_at: datetime = Field(description="Data e hora de criação do gênero.")
    updated_at: datetime = Field(description="Data e hora da última atualização do gênero.")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "M",
                "long_name": "Masculino",
                "created_at": "2024-05-25T10:00:00Z",
                "updated_at": "2024-05-25T10:00:00Z"
            }
        }

class MessageResponse(BaseModel):
    message: str = Field(description="Mensagem de resposta da operação.")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Operação realizada com sucesso."
            }
        }