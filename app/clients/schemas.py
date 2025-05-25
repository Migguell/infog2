from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
import uuid
from app.auth.schemas import Token

class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Nome completo do cliente.")
    email: EmailStr = Field(..., description="Endereço de e-mail único do cliente.")
    cpf: str = Field(..., min_length=11, max_length=11, description="CPF do cliente, contendo exatamente 11 dígitos numéricos.")
    password: str = Field(..., min_length=6, description="Senha para acesso do cliente, com no mínimo 6 caracteres.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Maria Souza",
                "email": "maria.souza@example.com",
                "cpf": "09876543211",
                "password": "outrasenha456"
            }
        }
    )

class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Novo nome completo do cliente (opcional).")
    email: Optional[EmailStr] = Field(None, description="Novo endereço de e-mail do cliente (opcional).")
    cpf: Optional[str] = Field(None, min_length=11, max_length=11, description="Novo CPF do cliente (opcional).")
    password: Optional[str] = Field(None, min_length=6, description="Nova senha para o cliente (opcional, mínimo 6 caracteres).")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Maria Oliveira Souza",
                "email": "maria.o.souza@example.com",
                "phone": "11987654321"
            }
        }
    )

class ClientResponse(BaseModel):
    id: uuid.UUID = Field(description="ID único do cliente.")
    name: str = Field(description="Nome completo do cliente.")
    email: EmailStr = Field(description="Endereço de e-mail do cliente.")
    cpf: str = Field(description="CPF do cliente.")
    created_at: datetime = Field(description="Data e hora de criação do registro do cliente.")
    updated_at: datetime = Field(description="Data e hora da última atualização do registro do cliente.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Maria Souza",
                "email": "maria.souza@example.com",
                "cpf": "09876543211",
                "created_at": "2024-05-25T14:00:00Z",
                "updated_at": "2024-05-25T14:05:00Z"
            }
        }
    )

class ClientCreateResponse(BaseModel):
    client: ClientResponse
    token: Token

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "client": getattr(getattr(ClientResponse, 'model_config', {}), 'get', lambda k,d: d)('json_schema_extra', {}).get('example', {}),
                "token": getattr(getattr(Token, 'model_config', {}), 'get', lambda k,d: d)('json_schema_extra', {}).get('example', {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjMGFkNmNkMy00ZDA1LTQxYmEtYWM0ZC1lNTMyYjQ1NGQzNmYiLCJpc19jbGllbnQiOnRydWUsImV4cCI6MTcyMTkwNDg2Nn0.exampleToken",
                    "token_type": "bearer"
                })
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