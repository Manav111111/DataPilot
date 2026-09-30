import asyncio
import logging
from typing import Optional
from app.core.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.collection.coordinator import CollectionJobCoordinator

logger = logging.getLogger(__name__)


async def _execute_collection_async(
    job_id: str, max_records: Optional[int] = None, max_queries: Optional[int] = None
):
    async with AsyncSessionLocal() as db:
        coordinator = CollectionJobCoordinator(db)
        await coordinator.run_collection(
            job_id=job_id,
            max_records_override=max_records,
            max_queries_override=max_queries,
        )


@celery_app.task(name="app.collection.tasks.run_collection_job_task", bind=True, max_retries=1)
def run_collection_job_task(
    self, job_id: str, max_records: Optional[int] = None, max_queries: Optional[int] = None
):
    """
    Celery background worker task for executing collection pipeline.
    """
    logger.info(f"Starting background Celery collection task for job_id={job_id}")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                _execute_collection_async(
                    job_id=job_id, max_records=max_records, max_queries=max_queries
                )
            )
        finally:
            loop.close()
        logger.info(f"Successfully finished collection task for job_id={job_id}")
    except Exception as exc:
        logger.exception(f"Collection task failed for job_id={job_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=10)


def dispatch_collection_job(
    job_id: str, max_records: Optional[int] = None, max_queries: Optional[int] = None
) -> None:
    """
    Dispatches a collection job to Celery, with graceful fallback to asyncio background task if Celery/Redis is unreachable.
    """
    from app.core.config import settings

    if settings.AI_PROVIDER == "mock":
        # In mock or test mode, run via asyncio without waiting for external broker
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                _execute_collection_async(
                    job_id=job_id, max_records=max_records, max_queries=max_queries
                )
            )
        except RuntimeError:
            asyncio.run(
                _execute_collection_async(
                    job_id=job_id, max_records=max_records, max_queries=max_queries
                )
            )
        return

    try:
        run_collection_job_task.delay(
            job_id=job_id, max_records=max_records, max_queries=max_queries
        )
        logger.info(f"Enqueued collection job {job_id} to Celery queue.")
    except Exception as e:
        logger.warning(
            f"Celery dispatch failed ({str(e)}). Falling back to asyncio background task."
        )
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                _execute_collection_async(
                    job_id=job_id, max_records=max_records, max_queries=max_queries
                )
            )
        except RuntimeError:
            # If no running event loop in thread, run synchronously
            asyncio.run(
                _execute_collection_async(
                    job_id=job_id, max_records=max_records, max_queries=max_queries
                )
            )

