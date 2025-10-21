from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.deps import get_current_active_user
from src.core.database import get_sync_session 
from src.models.user import User
from src.schemas.query import (
    Query as QuerySchema,
    QueryCreate,
    QueryUpdate,
    QueryListResponse
)
from src.services.query_service import QueryService

router = APIRouter()


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
        return query
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

    return query


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
