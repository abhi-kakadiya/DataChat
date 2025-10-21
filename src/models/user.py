import uuid

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.core.database import Base


class User(Base):
    """User model for authentication and user management."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    datasets = relationship("Dataset", back_populates="owner")
    queries = relationship("Query", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"
