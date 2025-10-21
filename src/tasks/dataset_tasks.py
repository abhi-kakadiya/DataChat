import asyncio
import logging
from typing import Any, Dict

from src.core.celery import celery_app
from src.core.database import SessionLocal
from src.models.dataset import Dataset
from src.services.dataset_service import DatasetService

logger = logging.getLogger(__name__)


async def _process_dataset_async(dataset_id: str, task_instance) -> Dict[str, Any]:
    """Async implementation of dataset processing."""
    dataset_service = DatasetService()
    
    task_instance.update_state(state="PROGRESS", meta={"progress": 10})
    
    db = SessionLocal()
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")

        dataset.status = "processing"
        db.commit()

        task_instance.update_state(state="PROGRESS", meta={"progress": 30})

        df = await dataset_service.get_dataset_data(dataset)

        task_instance.update_state(state="PROGRESS", meta={"progress": 60})

        dataset.row_count = len(df)
        dataset.column_count = len(df.columns)
        dataset.column_info = dataset_service._get_column_info(df)
        dataset.status = "ready"

        db.commit()

        task_instance.update_state(state="PROGRESS", meta={"progress": 100})

        return {
            "status": "success",
            "dataset_id": dataset_id,
            "row_count": len(df),
            "column_count": len(df.columns),
        }

    finally:
        db.close()


@celery_app.task(name="src.tasks.dataset_tasks.process_dataset", bind=True)
def process_dataset(self, dataset_id: str) -> Dict[str, Any]:
    """Process uploaded dataset - synchronous wrapper for async code."""
    try:
        return asyncio.run(_process_dataset_async(dataset_id, self))

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