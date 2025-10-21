from typing import Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    """Token response schema."""

    access_token: str = Field(..., description="Access token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenPayload(BaseModel):
    """Token payload schema."""

    sub: Optional[str] = Field(None, description="Subject (user ID)")


class UserLogin(BaseModel):
    """User login schema."""

    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")


class UserRegister(BaseModel):
    """User registration schema."""

    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    password: str = Field(..., description="User password")
