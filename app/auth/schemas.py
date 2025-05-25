from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
import uuid

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Nome completo do usuário.")
    cpf: str = Field(..., min_length=11, max_length=11, description="CPF do usuário, contendo exatamente 11 dígitos numéricos.")
    email: EmailStr = Field(..., description="Endereço de e-mail válido do usuário.")
    password: str = Field(..., min_length=6, description="Senha do usuário, com no mínimo 6 caracteres.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "name": "João da Silva",
                "cpf": "12345678901",
                "email": "joao.silva@example.com",
                "password": "senhaSegura123"
            }
        }
    )

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="Endereço de e-mail do usuário para login.")
    password: str = Field(..., description="Senha do usuário para login.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "joao.silva@example.com",
                "password": "senhaSegura123"
            }
        }
    )

class Token(BaseModel):
    access_token: str = Field(description="Token de acesso JWT.")
    token_type: str = Field("bearer", description="Tipo do token (sempre 'bearer').")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
                "token_type": "bearer"
            }
        }
    )

class TokenData(BaseModel):
    user_id: Optional[uuid.UUID] = Field(None, description="ID do usuário extraído do token.")
    is_admin: Optional[bool] = Field(False, description="Indica se o usuário no token é administrador.")

class UserResponse(BaseModel):
    id: uuid.UUID = Field(description="ID único do usuário.")
    name: str = Field(description="Nome completo do usuário.")
    cpf: str = Field(description="CPF do usuário.")
    email: EmailStr = Field(description="Endereço de e-mail do usuário.")
    is_active: bool = Field(description="Indica se o usuário está ativo.")
    is_admin: bool = Field(description="Indica se o usuário é um administrador.")
    created_at: datetime = Field(description="Data e hora de criação do registro do usuário.")
    updated_at: datetime = Field(description="Data e hora da última atualização do registro do usuário.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "name": "João da Silva",
                "cpf": "12345678901",
                "email": "joao.silva@example.com",
                "is_active": True,
                "is_admin": False,
                "created_at": "2024-05-24T10:30:00Z",
                "updated_at": "2024-05-24T10:30:00Z"
            }
        }
    )