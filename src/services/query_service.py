"""Service for processing natural language queries using DSPy."""

import logging
import time
from typing import Optional, List
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.models.query import Query
from src.models.dataset import Dataset
from src.schemas.query import QueryCreate
from src.dspy_modules import configure_dspy, generate_sql_query
from src.dspy_modules.nl_to_sql import NLToSQL
from src.services.dataset_service import DatasetService, sanitize_for_postgres_json

logger = logging.getLogger(__name__)


class QueryService:
    """Service for natural language query processing with DSPy."""

    def __init__(self):
        """Initialize query service with DSPy configuration."""
        self.dataset_service = DatasetService()
        self.nl_to_sql_module: Optional[NLToSQL] = None

        try:
            configure_dspy()
            self.nl_to_sql_module = NLToSQL()
            logger.info("DSPy configured successfully for QueryService")
        except Exception as e:
            logger.error(f"Failed to configure DSPy: {e}")
            self.nl_to_sql_module = None

    async def create_and_execute_query(
        self,
        db: Session,
        query_data: QueryCreate,
        user_id: str
    ) -> Query:
        """Create and execute a natural language query.

        Args:
            db: Database session
            query_data: Query creation data
            user_id: ID of the user making the query

        Returns:
            Created Query object with results
        """
        import uuid
        query = Query(
            id=str(uuid.uuid4()),
            user_id=user_id,
            dataset_id=query_data.dataset_id,
            natural_language_query=query_data.natural_language_query,
            status="pending"
        )
        db.add(query)
        db.commit()
        db.refresh(query)

        try:
            dataset = db.execute(
                select(Dataset).where(Dataset.id == query_data.dataset_id)
            ).scalar_one_or_none()

            if not dataset:
                raise ValueError(f"Dataset {query_data.dataset_id} not found")

            if dataset.status != "ready":
                raise ValueError(f"Dataset is not ready (status: {dataset.status})")

            df = await self.dataset_service.get_dataset_data(dataset)

            start_time = time.time()
            result = generate_sql_query(
                df=df,
                natural_language_query=query_data.natural_language_query,
                nl_to_sql_module=self.nl_to_sql_module
            )
            execution_time = time.time() - start_time

            if not result["success"]:
                query.status = "error"
                query.error_message = result["error"]
                query.generated_sql = result["sql_query"]
                query.query_type = result["query_type"]
                db.commit()
                db.refresh(query)
                return query

            result_df = result["result"]
            result_data = self._dataframe_to_json(result_df)

            query.generated_sql = result["sql_query"]
            query.query_type = result["query_type"]
            query.result_data = sanitize_for_postgres_json(result_data)
            query.result_summary = result["explanation"]
            query.execution_time = execution_time
            query.row_count = len(result_df)
            query.status = "success"

            db.commit()
            db.refresh(query)

            logger.info(
                f"Query {query.id} executed successfully in {execution_time:.2f}s, "
                f"returned {query.row_count} rows"
            )

            return query

        except Exception as e:
            logger.error(f"Query execution failed: {e}", exc_info=True)
            query.status = "error"
            query.error_message = str(e)
            db.commit()
            db.refresh(query)
            return query

    def get_user_queries(
        self,
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Query]:
        """Get queries for a user.

        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Query objects
        """
        queries = db.execute(
            select(Query)
            .where(Query.user_id == user_id)
            .order_by(Query.created_at.desc())
            .offset(skip)
            .limit(limit)
        ).scalars().all()

        return list(queries)

    def get_dataset_queries(
        self,
        db: Session,
        dataset_id: str,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Query]:
        """Get queries for a specific dataset.

        Args:
            db: Database session
            dataset_id: Dataset ID
            user_id: User ID (for authorization)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Query objects
        """
        dataset = db.execute(
            select(Dataset).where(
                Dataset.id == dataset_id,
                Dataset.owner_id == user_id
            )
        ).scalar_one_or_none()

        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found or unauthorized")

        queries = db.execute(
            select(Query)
            .where(Query.dataset_id == dataset_id)
            .order_by(Query.created_at.desc())
            .offset(skip)
            .limit(limit)
        ).scalars().all()

        return list(queries)

    def get_query(
        self,
        db: Session,
        query_id: str,
        user_id: str
    ) -> Optional[Query]:
        """Get a specific query by ID.

        Args:
            db: Database session
            query_id: Query ID
            user_id: User ID (for authorization)

        Returns:
            Query object or None
        """
        query = db.execute(
            select(Query)
            .where(Query.id == query_id, Query.user_id == user_id)
        ).scalar_one_or_none()

        return query

    def update_query_feedback(
        self,
        db: Session,
        query_id: str,
        user_id: str,
        feedback: str
    ) -> Optional[Query]:
        """Update user feedback for a query.

        Args:
            db: Database session
            query_id: Query ID
            user_id: User ID (for authorization)
            feedback: Feedback value (thumbs_up, thumbs_down, none)

        Returns:
            Updated Query object or None
        """
        query = db.execute(
            select(Query)
            .where(Query.id == query_id, Query.user_id == user_id)
        ).scalar_one_or_none()

        if not query:
            return None

        query.user_feedback = feedback
        db.commit()
        db.refresh(query)

        return query

    @staticmethod
    def _dataframe_to_json(df: pd.DataFrame) -> List[dict]:
        """Convert DataFrame to JSON-serializable list of dicts.

        Args:
            df: Input DataFrame

        Returns:
            List of dictionaries
        """
        max_rows = 1000
        if len(df) > max_rows:
            df = df.head(max_rows)

        result = df.to_dict(orient="records")
        return result
