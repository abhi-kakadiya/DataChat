from typing import Any, List

from fastapi import APIRouter, Depends, Form, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.api.deps import get_async_session, get_current_active_user
from src.models.user import User
from src.models.dataset import Dataset
from src.schemas.dataset import Dataset as DatasetSchema, DatasetCreate, DatasetPreview
from src.services.dataset_service import DatasetService
from src.tasks.dataset_tasks import process_dataset

router = APIRouter()


@router.post("/upload", response_model=DatasetSchema)
async def create_dataset(
    *,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(...),
) -> Any:
    """Create a new dataset."""
    allowed_extensions = [".csv", ".xlsx"]
    if not any(file.filename.endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV and XLSX files are supported",
        )

    dataset_data = DatasetCreate(name=name, description=description)

    dataset_service = DatasetService()
    dataset = await dataset_service.upload_dataset(
        file, dataset_data, str(current_user.id)
    )

    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)

    process_dataset.delay(str(dataset.id))

    return dataset


@router.get("/", response_model=List[DatasetSchema])
async def read_datasets(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Retrieve datasets."""
    result = await db.execute(
        select(Dataset)
        .where(Dataset.owner_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    datasets = result.scalars().all()

    return datasets


@router.get("/{dataset_id}", response_model=DatasetSchema)
async def read_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get dataset by ID."""
    result = await db.execute(
        select(Dataset)
        .where(Dataset.id == dataset_id)
        .where(Dataset.owner_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )

    return dataset


@router.get("/{dataset_id}/preview", response_model=DatasetPreview)
async def preview_dataset(
    dataset_id: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get dataset preview."""
    result = await db.execute(
        select(Dataset)
        .where(Dataset.id == dataset_id)
        .where(Dataset.owner_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )

    dataset_service = DatasetService()
    preview = await dataset_service.get_dataset_preview(dataset, limit)

    return preview


@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Delete dataset."""
    result = await db.execute(
        select(Dataset)
        .where(Dataset.id == dataset_id)
        .where(Dataset.owner_id == current_user.id)
    )
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )

    dataset_service = DatasetService()
    await dataset_service.storage.delete_file(dataset.file_path.split("/", 1)[1])

    await db.delete(dataset)
    await db.commit()

    return {"message": "Dataset deleted successfully"}
