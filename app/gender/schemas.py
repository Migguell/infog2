from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class GenderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=20)
    long_name: Optional[str] = Field(None, max_length=50)

class GenderUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=20)
    long_name: Optional[str] = Field(None, max_length=50)

class GenderResponse(BaseModel):
    id: int
    name: str
    long_name: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

