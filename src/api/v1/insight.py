"""Insight API endpoints for AI-generated data insights."""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from src.api.deps import get_sync_session, get_current_active_user
from src.models.user import User
from src.schemas.insight import (
    Insight as InsightSchema,
    InsightCreate,
    InsightListResponse
)
from src.services.insight_service import InsightService

router = APIRouter()


@router.post("/", response_model=InsightSchema, status_code=status.HTTP_201_CREATED)
def create_insight(
    *,
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_active_user),
    insight_in: InsightCreate,
) -> Any:
    """
    Create a manual insight.
    """
    insight_service = InsightService()

    try:
        insight = insight_service.create_insight(
            db=db,
            insight_data=insight_in
        )
        return insight
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create insight: {str(e)}"
        )


@router.post("/generate/dataset/{dataset_id}", response_model=List[InsightSchema])
async def generate_dataset_insights(
    dataset_id: str,
    max_insights: int = 5,
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Generate insights for a dataset using DSPy.

    This endpoint analyzes the dataset and generates AI-powered insights including:
    - Correlations between variables
    - Distribution patterns
    - Anomaly detection
    - Trend analysis
    """
    # Verify dataset ownership
    from sqlalchemy import select
    from src.models.dataset import Dataset

    dataset = db.execute(
        select(Dataset).where(
            Dataset.id == dataset_id,
            Dataset.owner_id == str(current_user.id)
        )
    ).scalar_one_or_none()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )

    insight_service = InsightService()

    try:
        insights = await insight_service.generate_dataset_insights(
            db=db,
            dataset_id=dataset_id,
            max_insights=max_insights
        )
        return insights
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate insights: {str(e)}"
        )


@router.post("/generate/query/{query_id}", response_model=List[InsightSchema])
async def generate_query_insights(
    query_id: str,
    max_insights: int = 3,
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Generate insights related to a specific query.
    """
    # Verify query ownership
    from sqlalchemy import select
    from src.models.query import Query

    query = db.execute(
        select(Query).where(
            Query.id == query_id,
            Query.user_id == str(current_user.id)
        )
    ).scalar_one_or_none()

    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found"
        )

    insight_service = InsightService()

    try:
        insights = await insight_service.generate_query_insights(
            db=db,
            query_id=query_id,
            max_insights=max_insights
        )
        return insights
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate insights: {str(e)}"
        )


@router.get("/dataset/{dataset_id}", response_model=InsightListResponse)
def list_dataset_insights(
    dataset_id: str,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve insights for a specific dataset.
    """
    # Verify dataset ownership
    from sqlalchemy import select, func
    from src.models.dataset import Dataset
    from src.models.insight import Insight

    dataset = db.execute(
        select(Dataset).where(
            Dataset.id == dataset_id,
            Dataset.owner_id == str(current_user.id)
        )
    ).scalar_one_or_none()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )

    insight_service = InsightService()
    insights = insight_service.get_dataset_insights(
        db=db,
        dataset_id=dataset_id,
        skip=skip,
        limit=limit
    )

    # Get total count
    total = db.execute(
        select(func.count(Insight.id)).where(Insight.dataset_id == dataset_id)
    ).scalar()

    return InsightListResponse(
        insights=insights,
        total=total or 0,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit
    )


@router.get("/query/{query_id}", response_model=List[InsightSchema])
def list_query_insights(
    query_id: str,
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve insights for a specific query.
    """
    # Verify query ownership
    from sqlalchemy import select
    from src.models.query import Query

    query = db.execute(
        select(Query).where(
            Query.id == query_id,
            Query.user_id == str(current_user.id)
        )
    ).scalar_one_or_none()

    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found"
        )

    insight_service = InsightService()
    insights = insight_service.get_query_insights(
        db=db,
        query_id=query_id
    )

    return insights


@router.get("/{insight_id}", response_model=InsightSchema)
def get_insight(
    insight_id: str,
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get a specific insight by ID.
    """
    insight_service = InsightService()
    insight = insight_service.get_insight(
        db=db,
        insight_id=insight_id
    )

    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insight not found"
        )

    # Verify access (insight belongs to user's dataset)
    from sqlalchemy import select
    from src.models.dataset import Dataset

    dataset = db.execute(
        select(Dataset).where(
            Dataset.id == insight.dataset_id,
            Dataset.owner_id == str(current_user.id)
        )
    ).scalar_one_or_none()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return insight


@router.delete("/{insight_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_insight(
    insight_id: str,
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """
    Delete an insight.
    """
    insight_service = InsightService()

    # Verify access first
    insight = insight_service.get_insight(db=db, insight_id=insight_id)
    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insight not found"
        )

    # Verify ownership
    from sqlalchemy import select
    from src.models.dataset import Dataset

    dataset = db.execute(
        select(Dataset).where(
            Dataset.id == insight.dataset_id,
            Dataset.owner_id == str(current_user.id)
        )
    ).scalar_one_or_none()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Delete
    deleted = insight_service.delete_insight(db=db, insight_id=insight_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete insight"
        )
