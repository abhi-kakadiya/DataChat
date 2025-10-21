"""Background tasks for DSPy model optimization and analytics."""

import logging
from datetime import datetime, timedelta

from src.core.celery import celery_app
from src.core.database import SessionLocal
from src.core.config import get_settings
from src.models.query import Query
from src.models.dataset import Dataset
from sqlalchemy import select, func

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.analytics.update_dspy_models")
def update_dspy_models():
    """
    Update and optimize DSPy modules using collected user feedback.

    This task:
    1. Collects queries with user feedback
    2. Uses successful queries as training examples
    3. Re-optimizes DSPy prompts using BootstrapFewShot
    4. Saves optimized models for improved performance
    """
    logger.info("Starting DSPy model optimization task")

    db = SessionLocal()
    settings = get_settings()

    try:
        # Collect training examples from successful queries with positive feedback
        training_queries = db.execute(
            select(Query).where(
                Query.status == "success",
                Query.user_feedback == "thumbs_up"
            ).limit(settings.DSPY_MAX_TRAIN_SIZE)
        ).scalars().all()

        logger.info(f"Found {len(training_queries)} positive training examples")

        if len(training_queries) < 10:
            logger.warning("Not enough training examples to optimize DSPy models")
            return {
                "status": "skipped",
                "reason": "insufficient_training_data",
                "examples_found": len(training_queries)
            }

        # Collect dev examples (queries with any feedback)
        dev_queries = db.execute(
            select(Query).where(
                Query.status == "success",
                Query.user_feedback.in_(["thumbs_up", "thumbs_down"])
            ).limit(settings.DSPY_MAX_DEV_SIZE)
        ).scalars().all()

        logger.info(f"Found {len(dev_queries)} dev examples")

        # TODO: Implement actual DSPy optimization
        # This would involve:
        # 1. Loading the NLToSQL module
        # 2. Creating training examples in DSPy format
        # 3. Running BootstrapFewShot or MIPRO optimizer
        # 4. Saving optimized prompts
        #
        # For now, we log the intent
        logger.info(
            f"Would optimize DSPy models with {len(training_queries)} training examples "
            f"and {len(dev_queries)} dev examples"
        )

        # Calculate metrics
        total_queries = db.execute(
            select(func.count(Query.id))
        ).scalar()

        successful_queries = db.execute(
            select(func.count(Query.id)).where(Query.status == "success")
        ).scalar()

        success_rate = (successful_queries / total_queries * 100) if total_queries > 0 else 0

        logger.info(
            f"Current performance: {successful_queries}/{total_queries} queries successful "
            f"({success_rate:.1f}% success rate)"
        )

        return {
            "status": "completed",
            "training_examples": len(training_queries),
            "dev_examples": len(dev_queries),
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "success_rate": success_rate
        }

    except Exception as e:
        logger.error(f"DSPy model optimization failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


@celery_app.task(name="app.tasks.analytics.generate_usage_stats")
def generate_usage_stats():
    """
    Generate usage statistics and analytics.

    This task collects metrics about:
    - Number of queries per day
    - Most popular datasets
    - Query success rates
    - Average execution times
    """
    logger.info("Generating usage statistics")

    db = SessionLocal()
    try:
        # Get date range (last 7 days)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)

        # Count queries by day
        queries_per_day = {}
        for i in range(7):
            day = start_date + timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)

            count = db.execute(
                select(func.count(Query.id)).where(
                    Query.created_at >= day_start,
                    Query.created_at < day_end
                )
            ).scalar()

            queries_per_day[day.strftime("%Y-%m-%d")] = count or 0

        # Most queried datasets
        from sqlalchemy import desc

        popular_datasets = db.execute(
            select(
                Dataset.id,
                Dataset.name,
                func.count(Query.id).label("query_count")
            )
            .join(Query, Query.dataset_id == Dataset.id)
            .where(Query.created_at >= start_date)
            .group_by(Dataset.id, Dataset.name)
            .order_by(desc("query_count"))
            .limit(10)
        ).all()

        # Overall metrics
        total_queries = db.execute(
            select(func.count(Query.id)).where(Query.created_at >= start_date)
        ).scalar() or 0

        successful_queries = db.execute(
            select(func.count(Query.id)).where(
                Query.created_at >= start_date,
                Query.status == "success"
            )
        ).scalar() or 0

        avg_execution_time = db.execute(
            select(func.avg(Query.execution_time)).where(
                Query.created_at >= start_date,
                Query.status == "success"
            )
        ).scalar() or 0

        stats = {
            "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "queries_per_day": queries_per_day,
            "popular_datasets": [
                {"id": d.id, "name": d.name, "query_count": d.query_count}
                for d in popular_datasets
            ],
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "success_rate": (successful_queries / total_queries * 100) if total_queries > 0 else 0,
            "avg_execution_time": float(avg_execution_time)
        }

        logger.info(f"Usage stats generated: {total_queries} queries, {stats['success_rate']:.1f}% success rate")

        return stats

    except Exception as e:
        logger.error(f"Failed to generate usage stats: {e}", exc_info=True)
        raise
    finally:
        db.close()
