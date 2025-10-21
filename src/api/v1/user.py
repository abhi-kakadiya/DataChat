"""User endpoints."""

from typing import Any, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_async_session, get_current_active_user, get_current_superuser
from src.models.user import User
from src.schemas.user import User as UserSchema

router = APIRouter()


@router.get("/me", response_model=UserSchema)
async def read_user_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get current user."""
    return current_user


@router.get("/", response_model=List[UserSchema])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_superuser),
) -> Any:
    """Retrieve users."""
    from sqlalchemy import select

    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()

    return users
