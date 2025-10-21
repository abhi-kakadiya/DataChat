"""Service for generating data insights using DSPy."""

import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.models.insight import Insight
from src.models.dataset import Dataset
from src.models.query import Query
from src.schemas.insight import InsightCreate
from src.dspy_modules import configure_dspy, generate_insights
from src.dspy_modules.insight_generator import InsightGenerator
from src.services.dataset_service import DatasetService, sanitize_for_postgres_json

logger = logging.getLogger(__name__)


class InsightService:
    """Service for automatic insight generation with DSPy."""

    def __init__(self):
        """Initialize insight service with DSPy configuration."""
        self.dataset_service = DatasetService()
        self.insight_generator: Optional[InsightGenerator] = None

        # Configure DSPy on initialization
        try:
            configure_dspy()
            self.insight_generator = InsightGenerator()
            logger.info("DSPy configured successfully for InsightService")
        except Exception as e:
            logger.error(f"Failed to configure DSPy: {e}")
            self.insight_generator = None

    async def generate_dataset_insights(
        self,
        db: Session,
        dataset_id: str,
        max_insights: int = 5
    ) -> List[Insight]:
        """Generate insights for a dataset.

        Args:
            db: Database session
            dataset_id: Dataset ID
            max_insights: Maximum number of insights to generate

        Returns:
            List of created Insight objects
        """
        try:
            # Get dataset
            dataset = db.execute(
                select(Dataset).where(Dataset.id == dataset_id)
            ).scalar_one_or_none()

            if not dataset:
                raise ValueError(f"Dataset {dataset_id} not found")

            if dataset.status != "ready":
                logger.warning(f"Dataset {dataset_id} is not ready (status: {dataset.status})")
                return []

            # Load dataset as DataFrame
            df = await self.dataset_service.get_dataset_data(dataset)

            # Generate insights using DSPy
            insights_data = generate_insights(
                df=df,
                query_context="",
                insight_generator=self.insight_generator,
                max_insights=max_insights
            )

            # Create insight records
            created_insights = []
            import uuid

            for insight_data in insights_data:
                # Generate visualization config based on insight type
                viz_config = self._generate_visualization_config(
                    insight_data["insight_type"],
                    insight_data.get("supporting_data", [])
                )

                insight = Insight(
                    id=str(uuid.uuid4()),
                    dataset_id=dataset_id,
                    query_id=None,
                    insight_type=insight_data["insight_type"],
                    title=insight_data["title"][:200],  # Limit title length
                    description=insight_data["description"],
                    confidence_score=insight_data["confidence_score"],
                    supporting_data=sanitize_for_postgres_json(insight_data.get("supporting_data")),
                    visualization_config=sanitize_for_postgres_json(viz_config)
                )
                db.add(insight)
                created_insights.append(insight)

            db.commit()

            logger.info(f"Generated {len(created_insights)} insights for dataset {dataset_id}")
            return created_insights

        except Exception as e:
            logger.error(f"Failed to generate insights for dataset {dataset_id}: {e}", exc_info=True)
            return []

    async def generate_query_insights(
        self,
        db: Session,
        query_id: str,
        max_insights: int = 3
    ) -> List[Insight]:
        """Generate insights related to a specific query.

        Args:
            db: Database session
            query_id: Query ID
            max_insights: Maximum number of insights to generate

        Returns:
            List of created Insight objects
        """
        try:
            # Get query with dataset
            query = db.execute(
                select(Query).where(Query.id == query_id)
            ).scalar_one_or_none()

            if not query or query.status != "success":
                logger.warning(f"Query {query_id} not found or not successful")
                return []

            # Get dataset
            dataset = db.execute(
                select(Dataset).where(Dataset.id == query.dataset_id)
            ).scalar_one_or_none()

            if not dataset or dataset.status != "ready":
                return []

            # Load dataset as DataFrame
            df = await self.dataset_service.get_dataset_data(dataset)

            # Generate insights with query context
            query_context = f"User asked: '{query.natural_language_query}'. Query returned {query.row_count} rows."

            insights_data = generate_insights(
                df=df,
                query_context=query_context,
                insight_generator=self.insight_generator,
                max_insights=max_insights
            )

            # Create insight records
            created_insights = []
            import uuid

            for insight_data in insights_data:
                viz_config = self._generate_visualization_config(
                    insight_data["insight_type"],
                    insight_data.get("supporting_data", [])
                )

                insight = Insight(
                    id=str(uuid.uuid4()),
                    dataset_id=dataset.id,
                    query_id=query_id,
                    insight_type=insight_data["insight_type"],
                    title=insight_data["title"][:200],
                    description=insight_data["description"],
                    confidence_score=insight_data["confidence_score"],
                    supporting_data=sanitize_for_postgres_json(insight_data.get("supporting_data")),
                    visualization_config=sanitize_for_postgres_json(viz_config)
                )
                db.add(insight)
                created_insights.append(insight)

            db.commit()

            logger.info(f"Generated {len(created_insights)} insights for query {query_id}")
            return created_insights

        except Exception as e:
            logger.error(f"Failed to generate insights for query {query_id}: {e}", exc_info=True)
            return []

    def create_insight(
        self,
        db: Session,
        insight_data: InsightCreate
    ) -> Insight:
        """Create a manual insight.

        Args:
            db: Database session
            insight_data: Insight creation data

        Returns:
            Created Insight object
        """
        import uuid

        insight = Insight(
            id=str(uuid.uuid4()),
            dataset_id=insight_data.dataset_id,
            query_id=insight_data.query_id,
            insight_type=insight_data.insight_type,
            title=insight_data.title,
            description=insight_data.description,
            confidence_score=insight_data.confidence_score,
            supporting_data=sanitize_for_postgres_json(insight_data.supporting_data),
            visualization_config=sanitize_for_postgres_json(insight_data.visualization_config)
        )
        db.add(insight)
        db.commit()
        db.refresh(insight)

        return insight

    def get_dataset_insights(
        self,
        db: Session,
        dataset_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Insight]:
        """Get insights for a dataset.

        Args:
            db: Database session
            dataset_id: Dataset ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Insight objects
        """
        insights = db.execute(
            select(Insight)
            .where(Insight.dataset_id == dataset_id)
            .order_by(Insight.confidence_score.desc(), Insight.created_at.desc())
            .offset(skip)
            .limit(limit)
        ).scalars().all()

        return list(insights)

    def get_query_insights(
        self,
        db: Session,
        query_id: str
    ) -> List[Insight]:
        """Get insights for a specific query.

        Args:
            db: Database session
            query_id: Query ID

        Returns:
            List of Insight objects
        """
        insights = db.execute(
            select(Insight)
            .where(Insight.query_id == query_id)
            .order_by(Insight.confidence_score.desc())
        ).scalars().all()

        return list(insights)

    def get_insight(
        self,
        db: Session,
        insight_id: str
    ) -> Optional[Insight]:
        """Get a specific insight by ID.

        Args:
            db: Database session
            insight_id: Insight ID

        Returns:
            Insight object or None
        """
        insight = db.execute(
            select(Insight).where(Insight.id == insight_id)
        ).scalar_one_or_none()

        return insight

    def delete_insight(
        self,
        db: Session,
        insight_id: str
    ) -> bool:
        """Delete an insight.

        Args:
            db: Database session
            insight_id: Insight ID

        Returns:
            True if deleted, False if not found
        """
        insight = db.execute(
            select(Insight).where(Insight.id == insight_id)
        ).scalar_one_or_none()

        if not insight:
            return False

        db.delete(insight)
        db.commit()
        return True

    @staticmethod
    def _generate_visualization_config(
        insight_type: str,
        supporting_data: list
    ) -> dict:
        """Generate visualization configuration based on insight type.

        Args:
            insight_type: Type of insight
            supporting_data: Supporting data for the insight

        Returns:
            Visualization config dict (Chart.js format)
        """
        # Default config
        config = {
            "type": "bar",
            "data": {
                "labels": [],
                "datasets": []
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "legend": {"display": True},
                    "title": {"display": False}
                }
            }
        }

        if not supporting_data:
            return config

        # Customize based on insight type
        if insight_type == "correlation":
            config["type"] = "scatter"
            if isinstance(supporting_data, list) and len(supporting_data) > 0:
                first_item = supporting_data[0]
                if isinstance(first_item, dict):
                    config["data"]["datasets"] = [{
                        "label": f"{first_item.get('col1', '')} vs {first_item.get('col2', '')}",
                        "data": []
                    }]

        elif insight_type == "trend":
            config["type"] = "line"
            if isinstance(supporting_data, list) and len(supporting_data) > 0:
                first_item = supporting_data[0]
                if isinstance(first_item, dict):
                    config["data"]["datasets"] = [{
                        "label": first_item.get("column", "Trend"),
                        "data": [],
                        "borderColor": "rgb(75, 192, 192)",
                        "tension": 0.1
                    }]

        elif insight_type == "distribution":
            config["type"] = "bar"
            if isinstance(supporting_data, list) and len(supporting_data) > 0:
                first_item = supporting_data[0]
                if isinstance(first_item, dict):
                    config["data"]["datasets"] = [{
                        "label": first_item.get("column", "Distribution"),
                        "data": []
                    }]

        elif insight_type == "anomaly":
            config["type"] = "scatter"
            config["options"]["plugins"]["title"]["text"] = "Outlier Detection"

        return config
