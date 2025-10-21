import logging
from typing import Any, Dict

from celery import current_task

from src.core.celery import celery_app
from src.core.database import SessionLocal
from src.models.dataset import Dataset
from src.services.dataset_service import DatasetService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
async def process_dataset(self, dataset_id: str) -> Dict[str, Any]:
    """Process uploaded dataset."""
    try:
        current_task.update_state(state="PROGRESS", meta={"progress": 10})
        db = SessionLocal()
        try:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if not dataset:
                raise ValueError(f"Dataset {dataset_id} not found")

            dataset.status = "processing"
            db.commit()

            current_task.update_state(state="PROGRESS", meta={"progress": 30})

            dataset_service = DatasetService()

            df = await dataset_service.get_dataset_data(dataset)

            current_task.update_state(state="PROGRESS", meta={"progress": 60})

            dataset.row_count = len(df)
            dataset.column_count = len(df.columns)
            dataset.column_info = dataset_service._get_column_info(df)
            dataset.status = "ready"

            db.commit()

            current_task.update_state(state="PROGRESS", meta={"progress": 100})

            return {
                "status": "success",
                "dataset_id": dataset_id,
                "row_count": len(df),
                "column_count": len(df.columns),
            }

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error processing dataset {dataset_id}: {str(e)}")

        db = SessionLocal()
        try:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if dataset:
                dataset.status = "error"
                dataset.error_message = str(e)
                db.commit()
        finally:
            db.close()

        raise
