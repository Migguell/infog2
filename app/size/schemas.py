from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SizeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=20)
    long_name: Optional[str] = Field(None, max_length=35)

class SizeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=20)
    long_name: Optional[str] = Field(None, max_length=35)

class SizeResponse(BaseModel):
    id: int
    name: str
    long_name: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    message: str