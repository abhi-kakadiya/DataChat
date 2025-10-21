"""Background tasks for data cleanup and maintenance."""

import logging
from datetime import datetime, timedelta

from src.core.celery import celery_app
from src.core.database import SessionLocal
from src.core.storage import storage_manager
from src.models.dataset import Dataset
from src.models.query import Query
from src.models.insight import Insight
from sqlalchemy import select, delete

logger = logging.getLogger(__name__)


@celery_app.task(name="src.tasks.data_processing.cleanup_old_files")
def cleanup_old_files():
    """
    Clean up old files and data.

    This task:
    1. Deletes datasets marked for deletion
    2. Removes old failed uploads (>7 days)
    3. Cleans up orphaned files in storage
    4. Removes old query results (>30 days)
    """
    logger.info("Starting cleanup task")

    db = SessionLocal()
    try:
        stats = {
            "datasets_deleted": 0,
            "files_deleted": 0,
            "old_queries_cleaned": 0,
            "orphaned_insights_cleaned": 0
        }

        # 1. Clean up failed datasets older than 7 days
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        failed_datasets = db.execute(
            select(Dataset).where(
                Dataset.status == "error",
                Dataset.created_at < cutoff_date
            )
        ).scalars().all()

        for dataset in failed_datasets:
            try:
                # Delete file from storage
                if dataset.file_path:
                    storage_manager.delete_file(dataset.file_path)
                    stats["files_deleted"] += 1

                # Delete database record
                db.delete(dataset)
                stats["datasets_deleted"] += 1

                logger.info(f"Deleted failed dataset {dataset.id}")
            except Exception as e:
                logger.error(f"Failed to delete dataset {dataset.id}: {e}")
                continue

        # 2. Clean up old query results (>30 days)
        query_cutoff_date = datetime.utcnow() - timedelta(days=30)
        old_queries = db.execute(
            select(Query).where(Query.created_at < query_cutoff_date)
        ).scalars().all()

        for query in old_queries:
            try:
                # Clear large result_data field but keep the query record
                query.result_data = None
                stats["old_queries_cleaned"] += 1
            except Exception as e:
                logger.error(f"Failed to clean query {query.id}: {e}")
                continue

        # 3. Clean up orphaned insights (where dataset was deleted)
        orphaned_insights = db.execute(
            select(Insight)
            .where(~Insight.dataset_id.in_(select(Dataset.id)))
        ).scalars().all()

        for insight in orphaned_insights:
            try:
                db.delete(insight)
                stats["orphaned_insights_cleaned"] += 1
            except Exception as e:
                logger.error(f"Failed to delete orphaned insight {insight.id}: {e}")
                continue

        # Commit all changes
        db.commit()

        logger.info(
            f"Cleanup completed: {stats['datasets_deleted']} datasets deleted, "
            f"{stats['files_deleted']} files deleted, "
            f"{stats['old_queries_cleaned']} old queries cleaned, "
            f"{stats['orphaned_insights_cleaned']} orphaned insights removed"
        )

        return stats

    except Exception as e:
        logger.error(f"Cleanup task failed: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(name="src.tasks.data_processing.vacuum_database")
def vacuum_database():
    """
    Perform database maintenance (PostgreSQL VACUUM).

    This helps reclaim storage and optimize query performance.
    """
    logger.info("Starting database vacuum task")

    db = SessionLocal()
    try:
        # PostgreSQL VACUUM cannot run inside a transaction
        db.connection().connection.set_isolation_level(0)
        db.execute("VACUUM ANALYZE")
        logger.info("Database vacuum completed successfully")
        return {"status": "completed"}
    except Exception as e:
        logger.error(f"Database vacuum failed: {e}", exc_info=True)
        raise
    finally:
        db.close()
