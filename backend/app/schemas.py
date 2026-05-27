from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime

class SpecResponse(BaseModel):
    id: UUID
    version: str
    is_active: bool
    is_deprecated: bool
    registered_at: datetime
    class Config:
        from_attributes = True

class ApiResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    versions: List[SpecResponse]
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "viewer" # По умолчанию создаем читателя

class UserResponse(BaseModel):
    id: UUID
    username: str
    role: str
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str