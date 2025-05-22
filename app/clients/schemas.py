from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid

class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    cpf: str = Field(..., min_length=11, max_length=11)
    address: Optional[str] = Field(None, max_length=500)

class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    cpf: Optional[str] = Field(None, min_length=11, max_length=11)
    address: Optional[str] = Field(None, max_length=500)

class ClientResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    cpf: str
    address: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

