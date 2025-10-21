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
    """Service for natural language query processing with DSPy and context handling."""

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
        """Create and execute a natural language query with context awareness.

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

            is_followup, previous_query = self._check_followup_query(
                db, query_data.natural_language_query, user_id, query_data.dataset_id
            )

            if is_followup and previous_query and previous_query.result_data:
                try:
                    result = self._handle_followup_query(
                        previous_query, query_data.natural_language_query, df
                    )
                    execution_time = 0.1  # Fast follow-up query
                    
                    query.generated_sql = result["sql_query"]
                    query.query_type = result["query_type"]
                    query.result_data = sanitize_for_postgres_json(result["result_data"])
                    query.result_summary = result["explanation"]
                    query.execution_time = execution_time
                    query.row_count = len(result["result_data"])
                    query.status = "success"
                    
                    db.commit()
                    db.refresh(query)
                    return query
                    
                except Exception as e:
                    logger.warning(f"Follow-up query handling failed, falling back to full query: {e}")

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

    def _check_followup_query(
        self,
        db: Session,
        query_text: str,
        user_id: str,
        dataset_id: str
    ) -> tuple[bool, Optional[Query]]:
        """Check if this is a follow-up query to sort/filter previous results.
        
        Returns:
            Tuple of (is_followup, previous_query)
        """
        followup_keywords = [
            "sort", "order", "arrange", "ranking",
            "highest", "lowest", "top", "bottom",
            "ascending", "descending", "desc", "asc",
            "filter", "show only", "exclude"
        ]
        
        query_lower = query_text.lower()
        is_followup = any(keyword in query_lower for keyword in followup_keywords)
        
        if not is_followup:
            return False, None
            
        previous_query = db.execute(
            select(Query)
            .where(
                Query.user_id == user_id,
                Query.dataset_id == dataset_id,
                Query.status == "success"
            )
            .order_by(Query.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        
        return True, previous_query

    def _handle_followup_query(
        self,
        previous_query: Query,
        followup_text: str,
        original_df: pd.DataFrame
    ) -> dict:
        """Handle follow-up queries like sorting or filtering previous results.
        
        Args:
            previous_query: The previous successful query
            followup_text: The follow-up query text
            original_df: Original dataset DataFrame
            
        Returns:
            Dictionary with query results
        """
        if not previous_query.result_data:
            raise ValueError("No previous results to operate on")
            
        result_df = pd.DataFrame(previous_query.result_data)
        
        followup_lower = followup_text.lower()
        
        if any(keyword in followup_lower for keyword in ["sort", "order", "arrange", "highest", "lowest", "top", "bottom"]):
            result_df = self._apply_sort(result_df, followup_lower)
            operation = "Sorted previous results"
            
        elif any(keyword in followup_lower for keyword in ["filter", "show only", "where", "exclude"]):
            result_df = self._apply_filter(result_df, followup_lower)
            operation = "Filtered previous results"
            
        else:
            raise ValueError("Could not determine follow-up operation")
        
        return {
            "sql_query": f"{previous_query.generated_sql} (then: {followup_text})",
            "query_type": "followup_" + previous_query.query_type,
            "result_data": result_df.to_dict('records'),
            "explanation": f"{operation} based on: {followup_text}"
        }

    def _apply_sort(self, df: pd.DataFrame, sort_text: str) -> pd.DataFrame:
        """Apply sorting to a DataFrame based on natural language.
        
        Args:
            df: DataFrame to sort
            sort_text: Natural language sort instruction
            
        Returns:
            Sorted DataFrame
        """
        ascending = "asc" in sort_text or "lowest" in sort_text or "bottom" in sort_text or "ascending" in sort_text
        descending = "desc" in sort_text or "highest" in sort_text or "top" in sort_text or "descending" in sort_text
        
        if descending:
            ascending = False
        elif not ascending:
            ascending = False
            
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if numeric_cols:
            sort_col = numeric_cols[0]
        else:
            sort_col = df.columns[0]
            
        for col in df.columns:
            if col.lower() in sort_text:
                sort_col = col
                break
        
        logger.info(f"Sorting by {sort_col}, ascending={ascending}")
        return df.sort_values(by=sort_col, ascending=ascending).reset_index(drop=True)

    def _apply_filter(self, df: pd.DataFrame, filter_text: str) -> pd.DataFrame:
        """Apply filtering to a DataFrame based on natural language.
        
        Args:
            df: DataFrame to filter
            filter_text: Natural language filter instruction
            
        Returns:
            Filtered DataFrame
        """
        import re
        
        greater_than_match = re.search(r'(?:greater than|more than|above|over)\s+(\d+)', filter_text)
        less_than_match = re.search(r'(?:less than|fewer than|below|under)\s+(\d+)', filter_text)
        equals_match = re.search(r'(?:equals?|exactly)\s+(\d+)', filter_text)
        
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if numeric_cols and greater_than_match:
            threshold = float(greater_than_match.group(1))
            df = df[df[numeric_cols[0]] > threshold]
        elif numeric_cols and less_than_match:
            threshold = float(less_than_match.group(1))
            df = df[df[numeric_cols[0]] < threshold]
        elif numeric_cols and equals_match:
            threshold = float(equals_match.group(1))
            df = df[df[numeric_cols[0]] == threshold]
        
        return df.reset_index(drop=True)

    def get_user_queries(
        self,
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Query]:
        """Get queries for a user."""
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
        """Get queries for a specific dataset."""
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
            .order_by(Query.created_at.asc())
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
        """Get a specific query by ID."""
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
        """Update user feedback for a query."""
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
        """Convert DataFrame to JSON-serializable list of dicts."""
        max_rows = 1000
        if len(df) > max_rows:
            df = df.head(max_rows)

        result = df.to_dict(orient="records")
        return result