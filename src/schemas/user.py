import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""
    
    email: EmailStr = Field(..., description="User email")
    username: str = Field(..., description="Username")
    is_active: bool = Field(default=True, description="Is user active")


class UserCreate(UserBase):
    """User creation schema."""
    
    password: str = Field(..., description="User password")


class UserUpdate(BaseModel):
    """User update schema."""
    
    email: Optional[EmailStr] = Field(None, description="User email")
    username: Optional[str] = Field(None, description="Username")
    is_active: Optional[bool] = Field(None, description="Is user active")
    password: Optional[str] = Field(None, description="User password")


class UserInDBBase(UserBase):
    """Base user in database schema."""
    
    id: uuid.UUID = Field(..., description="User ID")
    is_superuser: bool = Field(..., description="Is superuser")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserInDB(UserInDBBase):
    """User in database schema."""
    
    hashed_password: str = Field(..., description="Hashed password")


class User(UserInDBBase):
    """User response schema."""
    pass