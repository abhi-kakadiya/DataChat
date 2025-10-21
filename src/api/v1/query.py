"""Query API endpoints for natural language data analysis."""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.deps import get_sync_session, get_current_active_user
from src.models.user import User
from src.schemas.query import (
    Query as QuerySchema,
    QueryCreate,
    QueryUpdate,
    QueryListResponse
)
from src.services.query_service import QueryService

router = APIRouter()


def determine_visualization_type(query_obj: Any) -> str:
    """Determine visualization type based on query characteristics."""
    # If query failed, return table
    if query_obj.status != "success" or not query_obj.result_data:
        return "table"

    # Single value result
    if query_obj.row_count == 1 and len(query_obj.result_data[0]) == 1:
        return "number"

    # Check query type and structure
    query_type = (query_obj.query_type or "").lower()
    query_text = (query_obj.natural_language_query or "").lower()

    # Time series detection
    time_keywords = ["trend", "over time", "timeline", "history", "daily", "monthly", "yearly"]
    if any(keyword in query_text for keyword in time_keywords):
        return "line_chart"

    # Distribution/percentage detection
    dist_keywords = ["distribution", "percentage", "breakdown", "proportion", "share"]
    if any(keyword in query_text for keyword in dist_keywords):
        return "pie_chart"

    # Aggregation/comparison detection
    agg_keywords = ["group", "average", "sum", "count", "total", "top", "bottom", "highest", "lowest"]
    if any(keyword in query_text for keyword in agg_keywords) or "aggregation" in query_type or "grouping" in query_type:
        return "bar_chart"

    # Check result structure - if has 2-3 columns with one numeric, likely bar chart
    if query_obj.result_data and len(query_obj.result_data) > 0:
        first_row = query_obj.result_data[0]
        if 2 <= len(first_row) <= 3:
            return "bar_chart"

    # Default to table for complex data
    return "table"


@router.post("/", response_model=QuerySchema, status_code=status.HTTP_201_CREATED)
async def create_query(
    *,
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_active_user),
    query_in: QueryCreate,
) -> Any:
    """
    Create a new query and execute it using DSPy.

    This endpoint takes a natural language question and:
    1. Converts it to SQL using DSPy prompt engineering
    2. Executes the query on the specified dataset
    3. Returns results with explanations
    """
    query_service = QueryService()

    try:
        query = await query_service.create_and_execute_query(
            db=db,
            query_data=query_in,
            user_id=str(current_user.id)
        )

        # Convert to schema and add visualization type
        query_dict = {
            "id": query.id,
            "user_id": query.user_id,
            "dataset_id": query.dataset_id,
            "natural_language_query": query.natural_language_query,
            "generated_sql": query.generated_sql,
            "query_type": query.query_type,
            "result_data": query.result_data,
            "result_summary": query.result_summary,
            "execution_time": query.execution_time,
            "row_count": query.row_count,
            "status": query.status,
            "error_message": query.error_message,
            "user_feedback": query.user_feedback,
            "created_at": query.created_at,
            "updated_at": query.updated_at,
            "visualization_type": determine_visualization_type(query)
        }

        return QuerySchema(**query_dict)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )


@router.get("/", response_model=QueryListResponse)
def list_queries(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve user's queries with pagination.
    """
    query_service = QueryService()
    queries = query_service.get_user_queries(
        db=db,
        user_id=str(current_user.id),
        skip=skip,
        limit=limit
    )

    # Get total count
    from sqlalchemy import select, func
    from src.models.query import Query
    total = db.execute(
        select(func.count(Query.id)).where(Query.user_id == str(current_user.id))
    ).scalar()

    return QueryListResponse(
        queries=queries,
        total=total or 0,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit
    )


@router.get("/dataset/{dataset_id}", response_model=QueryListResponse)
def list_dataset_queries(
    dataset_id: str,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve queries for a specific dataset.
    """
    query_service = QueryService()

    try:
        queries = query_service.get_dataset_queries(
            db=db,
            dataset_id=dataset_id,
            user_id=str(current_user.id),
            skip=skip,
            limit=limit
        )

        # Get total count
        from sqlalchemy import select, func
        from src.models.query import Query
        total = db.execute(
            select(func.count(Query.id)).where(Query.dataset_id == dataset_id)
        ).scalar()

        return QueryListResponse(
            queries=queries,
            total=total or 0,
            page=skip // limit + 1 if limit > 0 else 1,
            page_size=limit
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{query_id}", response_model=QuerySchema)
def get_query(
    query_id: str,
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get a specific query by ID.
    """
    query_service = QueryService()
    query = query_service.get_query(
        db=db,
        query_id=query_id,
        user_id=str(current_user.id)
    )

    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found"
        )

    # Add visualization type to response
    query_dict = {
        "id": query.id,
        "user_id": query.user_id,
        "dataset_id": query.dataset_id,
        "natural_language_query": query.natural_language_query,
        "generated_sql": query.generated_sql,
        "query_type": query.query_type,
        "result_data": query.result_data,
        "result_summary": query.result_summary,
        "execution_time": query.execution_time,
        "row_count": query.row_count,
        "status": query.status,
        "error_message": query.error_message,
        "user_feedback": query.user_feedback,
        "created_at": query.created_at,
        "updated_at": query.updated_at,
        "visualization_type": determine_visualization_type(query)
    }

    return QuerySchema(**query_dict)


@router.patch("/{query_id}", response_model=QuerySchema)
def update_query(
    query_id: str,
    query_update: QueryUpdate,
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update query feedback (thumbs up/down).
    """
    query_service = QueryService()

    if query_update.user_feedback:
        query = query_service.update_query_feedback(
            db=db,
            query_id=query_id,
            user_id=str(current_user.id),
            feedback=query_update.user_feedback
        )

        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Query not found"
            )

        return query

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="No valid update data provided"
    )
