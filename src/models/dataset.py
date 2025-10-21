import uuid

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.core.database import Base


class Dataset(Base):
    """Dataset model."""

    __tablename__ = "datasets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)

    row_count = Column(Integer, nullable=True)
    column_count = Column(Integer, nullable=True)
    column_info = Column(JSON, nullable=True)

    status = Column(String(50), default="uploaded", nullable=False)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner_id = Column(String, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="datasets")
    queries = relationship("Query", back_populates="dataset")

    def __repr__(self) -> str:
        return f"<Dataset(id={self.id}, name={self.name}, status={self.status})>"
