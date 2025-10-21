import uuid

from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.core.database import Base


class Insight(Base):
    """Insight model for storing generated insights and analysis."""

    __tablename__ = "insights"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    query_id = Column(String, ForeignKey("queries.id"), nullable=True)

    insight_type = Column(String, nullable=False)  # trend, anomaly, correlation, etc.
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    confidence_score = Column(Float)  # 0.0 to 1.0

    supporting_data = Column(JSON)
    visualization_config = Column(JSON)  # Chart.js/Plotly configuration

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    dataset = relationship("Dataset")
    query = relationship("Query")

    def __repr__(self) -> str:
        return f"<Insight(id={self.id}, title={self.title}, insight_type={self.insight_type})>"
