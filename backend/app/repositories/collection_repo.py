from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc, or_
from sqlalchemy.orm import selectinload

from app.models.collection_job import CollectionJob
from app.models.collection_job_event import CollectionJobEvent
from app.models.dataset import Dataset
from app.models.dataset_record import DatasetRecord
from app.models.data_source import DataSource
from app.models.record_source import RecordSource


class CollectionJobRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, job: CollectionJob) -> CollectionJob:
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def get_by_id(self, job_id: str, user_id: Optional[str] = None) -> Optional[CollectionJob]:
        query = select(CollectionJob).where(CollectionJob.id == job_id)
        if user_id:
            query = query.where(CollectionJob.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_by_project(
        self,
        project_id: str,
        user_id: str,
        page: int = 1,
        size: int = 20,
        status: Optional[str] = None,
    ) -> Tuple[List[CollectionJob], int]:
        query = select(CollectionJob).where(
            CollectionJob.project_id == project_id,
            CollectionJob.user_id == user_id,
        )
        if status:
            query = query.where(CollectionJob.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(desc(CollectionJob.created_at)).offset((page - 1) * size).limit(size)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_events(
        self, job_id: str, user_id: str
    ) -> List[CollectionJobEvent]:
        # Validate job belongs to user
        job = await self.get_by_id(job_id, user_id)
        if not job:
            return []

        query = (
            select(CollectionJobEvent)
            .where(CollectionJobEvent.collection_job_id == job_id)
            .order_by(asc(CollectionJobEvent.created_at))
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())


class DatasetRecordRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_records(
        self,
        dataset_id: str,
        user_id: str,
        page: int = 1,
        size: int = 50,
        search: Optional[str] = None,
        validation_status: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ) -> Tuple[List[DatasetRecord], int]:
        # Ensure user owns dataset
        ds_query = select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == user_id)
        ds_res = await self.db.execute(ds_query)
        if not ds_res.scalar_one_or_none():
            return [], 0

        query = select(DatasetRecord).where(DatasetRecord.dataset_id == dataset_id)
        if validation_status:
            query = query.where(DatasetRecord.validation_status == validation_status)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        if sort_order.lower() == "asc":
            query = query.order_by(asc(DatasetRecord.created_at))
        else:
            query = query.order_by(desc(DatasetRecord.created_at))

        query = query.offset((page - 1) * size).limit(size)
        result = await self.db.execute(query)
        records = list(result.scalars().all())

        # If search term provided, filter in memory on JSON content if DB search not indexed
        if search:
            search_lower = search.lower()
            filtered = [
                r for r in records if search_lower in str(r.record_data).lower()
            ]
            return filtered, len(filtered)

        return records, total

    async def get_record_provenance(
        self, record_id: str, user_id: str
    ) -> List[Dict[str, Any]]:
        # Verify ownership via dataset and user
        query = (
            select(RecordSource, DataSource)
            .join(DatasetRecord, RecordSource.dataset_record_id == DatasetRecord.id)
            .join(Dataset, DatasetRecord.dataset_id == Dataset.id)
            .join(DataSource, RecordSource.data_source_id == DataSource.id)
            .where(RecordSource.dataset_record_id == record_id, Dataset.user_id == user_id)
        )
        result = await self.db.execute(query)
        rows = result.all()

        provenances = []
        for rs, ds in rows:
            provenances.append(
                {
                    "id": rs.id,
                    "dataset_record_id": rs.dataset_record_id,
                    "data_source_id": rs.data_source_id,
                    "evidence_excerpt": rs.evidence_excerpt,
                    "evidence_field": rs.evidence_field,
                    "source_url": ds.source_url,
                    "domain": ds.domain,
                    "page_title": ds.page_title,
                    "created_at": rs.created_at,
                }
            )
        return provenances

    async def list_sources(
        self,
        dataset_id: str,
        user_id: str,
        page: int = 1,
        size: int = 50,
        domain: Optional[str] = None,
        retrieval_status: Optional[str] = None,
    ) -> Tuple[List[DataSource], int]:
        # Ensure user owns dataset
        ds_query = select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == user_id)
        ds_res = await self.db.execute(ds_query)
        if not ds_res.scalar_one_or_none():
            return [], 0

        query = select(DataSource).where(DataSource.dataset_id == dataset_id)
        if domain:
            query = query.where(DataSource.domain == domain)
        if retrieval_status:
            query = query.where(DataSource.retrieval_status == retrieval_status)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        query = query.order_by(desc(DataSource.created_at)).offset((page - 1) * size).limit(size)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_dataset_overview_stats(
        self, dataset_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        ds_query = select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == user_id)
        ds_res = await self.db.execute(ds_query)
        dataset = ds_res.scalar_one_or_none()
        if not dataset:
            return None

        # Total records
        total_q = select(func.count()).where(DatasetRecord.dataset_id == dataset_id)
        total_records = (await self.db.execute(total_q)).scalar_one()

        # Valid records
        valid_q = select(func.count()).where(
            DatasetRecord.dataset_id == dataset_id, DatasetRecord.validation_status == "valid"
        )
        valid_records = (await self.db.execute(valid_q)).scalar_one()

        # Warning records
        warn_q = select(func.count()).where(
            DatasetRecord.dataset_id == dataset_id,
            DatasetRecord.validation_status == "valid_with_warnings",
        )
        records_with_warnings = (await self.db.execute(warn_q)).scalar_one()

        # Rejected/invalid records
        invalid_q = select(func.count()).where(
            DatasetRecord.dataset_id == dataset_id, DatasetRecord.validation_status == "invalid"
        )
        rejected_records = (await self.db.execute(invalid_q)).scalar_one()

        # Sources count
        sources_q = select(func.count()).where(DataSource.dataset_id == dataset_id)
        source_count = (await self.db.execute(sources_q)).scalar_one()

        # Latest job status
        latest_job_q = (
            select(CollectionJob.status)
            .where(CollectionJob.dataset_id == dataset_id)
            .order_by(desc(CollectionJob.created_at))
            .limit(1)
        )
        latest_job_status = (await self.db.execute(latest_job_q)).scalar_one_or_none()

        return {
            "total_records": total_records,
            "valid_records": valid_records,
            "records_with_warnings": records_with_warnings,
            "rejected_records": rejected_records,
            "duplicate_count": max(0, source_count - total_records) if source_count > total_records else 0,
            "source_count": source_count,
            "latest_job_status": latest_job_status,
        }
