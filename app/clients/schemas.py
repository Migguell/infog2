from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid
from app.auth.schemas import Token # Importar o schema de Token

class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    cpf: str = Field(..., min_length=11, max_length=11)
    password: str = Field(..., min_length=6)

class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    cpf: Optional[str] = Field(None, min_length=11, max_length=11)
    password: Optional[str] = Field(None, min_length=6)

class ClientResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    cpf: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ClientCreateResponse(BaseModel):
    client: ClientResponse
    token: Token
