"""Background tasks for insight generation."""

import logging
from datetime import datetime, timedelta

from src.core.celery import celery_app
from src.core.database import SessionLocal
from src.services.insight_service import InsightService
from src.models.dataset import Dataset
from sqlalchemy import select

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.insights.generate_background_insights")
def generate_background_insights():
    """
    Background task to generate insights for datasets that don't have recent insights.

    This task runs periodically (hourly) to automatically generate insights for datasets
    that have been updated or don't have insights yet.
    """
    logger.info("Starting background insight generation task")

    db = SessionLocal()
    try:
        insight_service = InsightService()

        # Find datasets that need insights
        # Criteria: ready status and either no insights or updated recently
        result = db.execute(
            select(Dataset).where(Dataset.status == "ready")
        )
        datasets = result.scalars().all()

        datasets_processed = 0
        insights_generated = 0

        for dataset in datasets:
            try:
                # Check if dataset has recent insights (within last 24 hours)
                from src.models.insight import Insight
                from sqlalchemy import func

                recent_insights_count = db.execute(
                    select(func.count(Insight.id))
                    .where(Insight.dataset_id == dataset.id)
                    .where(Insight.created_at >= datetime.utcnow() - timedelta(hours=24))
                ).scalar()

                # Skip if already has recent insights
                if recent_insights_count and recent_insights_count > 0:
                    logger.info(f"Dataset {dataset.id} already has recent insights, skipping")
                    continue

                # Generate insights asynchronously
                import asyncio
                insights = asyncio.run(
                    insight_service.generate_dataset_insights(
                        db=db,
                        dataset_id=dataset.id,
                        max_insights=5
                    )
                )

                datasets_processed += 1
                insights_generated += len(insights)

                logger.info(
                    f"Generated {len(insights)} insights for dataset {dataset.id} ({dataset.name})"
                )

            except Exception as e:
                logger.error(f"Failed to generate insights for dataset {dataset.id}: {e}")
                continue

        logger.info(
            f"Background insight generation completed: "
            f"{datasets_processed} datasets processed, "
            f"{insights_generated} insights generated"
        )

        return {
            "datasets_processed": datasets_processed,
            "insights_generated": insights_generated
        }

    except Exception as e:
        logger.error(f"Background insight generation task failed: {e}", exc_info=True)
        raise
    finally:
        db.close()
