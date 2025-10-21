import uuid

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.core.database import Base


class Query(Base):
    """Query model for storing user queries and their results."""

    __tablename__ = "queries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)

    natural_language_query = Column(Text, nullable=False)
    generated_sql = Column(Text)
    query_type = Column(String)  # aggregation, filtering, visualization, etc.

    result_data = Column(JSON)
    result_summary = Column(Text)
    execution_time = Column(Float)  # in seconds
    row_count = Column(Integer)

    status = Column(String, default="pending")  # pending, success, error
    error_message = Column(Text)
    user_feedback = Column(String)  # thumbs_up, thumbs_down, none

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="queries")
    dataset = relationship("Dataset", back_populates="queries")

    def __repr__(self) -> str:
        return f"<Query(id={self.id}, dataset_id={self.dataset_id}, query_type={self.query_type})>"
