import csv
import io
import json
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.collection_job import CollectionJob
from app.models.collection_job_event import CollectionJobEvent
from app.models.plan import CollectionPlan
from app.models.dataset import Dataset
from app.models.dataset_record import DatasetRecord
from app.models.data_source import DataSource
from app.repositories.collection_repo import CollectionJobRepository, DatasetRecordRepository
from app.schemas.collection import (
    StartCollectionRequest,
    StartCollectionResponse,
    CollectionJobResponse,
    CollectionJobListResponse,
    CollectionJobEventResponse,
    CollectionJobEventListResponse,
    DataSourceResponse,
    DataSourceListResponse,
    RecordSourceResponse,
    DatasetRecordResponse,
    DatasetRecordListResponse,
    DatasetOverviewStats,
)
from app.collection.tasks import dispatch_collection_job


class CollectionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.job_repo = CollectionJobRepository(db)
        self.record_repo = DatasetRecordRepository(db)

    async def start_collection(
        self, plan_id: str, user_id: str, request: StartCollectionRequest
    ) -> StartCollectionResponse:
        # 1. Verify Plan ownership and status
        plan_query = select(CollectionPlan).where(
            CollectionPlan.id == plan_id, CollectionPlan.user_id == user_id
        )
        plan_res = await self.db.execute(plan_query)
        plan = plan_res.scalar_one_or_none()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection plan not found",
            )

        if plan.status != "approved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only approved plans can start data collection. Current plan status is '{plan.status}'.",
            )

        plan_data = plan.plan_data or {}
        fields = plan_data.get("fields", [])
        if not fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Collection plan has no configured fields to extract.",
            )

        # 2. Create or link Dataset
        dataset_name = request.dataset_name or f"{plan_data.get('goal', 'Dataset')[:50]} - {datetime.now().strftime('%b %d %H:%M')}"
        dataset = Dataset(
            project_id=plan.project_id,
            user_id=user_id,
            name=dataset_name,
            description=f"Auto-generated from approved collection plan '{plan_data.get('goal', '')}'",
            status="collecting",
            row_count=0,
        )
        self.db.add(dataset)
        await self.db.flush()

        # 3. Create CollectionJob
        job = CollectionJob(
            user_id=user_id,
            project_id=plan.project_id,
            plan_id=plan.id,
            dataset_id=dataset.id,
            status="queued",
            current_stage="initializing",
            progress_percentage=0,
            total_queries=len(plan_data.get("search_queries", [])),
            records_extracted=0,
            records_saved=0,
            records_rejected=0,
        )
        await self.job_repo.create(job)

        # 4. Log initial event
        event = CollectionJobEvent(
            collection_job_id=job.id,
            event_type="info",
            message=f"Collection job queued for plan '{plan_data.get('goal', '')}'",
        )
        self.db.add(event)
        await self.db.commit()

        # 5. Dispatch background worker task
        dispatch_collection_job(
            job_id=job.id,
            max_records=request.max_records,
            max_queries=request.max_queries,
        )

        return StartCollectionResponse(
            job_id=job.id,
            dataset_id=dataset.id,
            status=job.status,
            message="Data collection job queued successfully",
        )

    async def get_job(self, job_id: str, user_id: str) -> CollectionJobResponse:
        job = await self.job_repo.get_by_id(job_id, user_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection job not found",
            )
        return CollectionJobResponse.model_validate(job)

    async def list_project_jobs(
        self,
        project_id: str,
        user_id: str,
        page: int = 1,
        size: int = 20,
        status_filter: Optional[str] = None,
    ) -> CollectionJobListResponse:
        items, total = await self.job_repo.list_by_project(
            project_id=project_id,
            user_id=user_id,
            page=page,
            size=size,
            status=status_filter,
        )
        pages = (total + size - 1) // size if total > 0 else 1
        return CollectionJobListResponse(
            items=[CollectionJobResponse.model_validate(j) for j in items],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def cancel_job(self, job_id: str, user_id: str) -> CollectionJobResponse:
        job = await self.job_repo.get_by_id(job_id, user_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection job not found",
            )

        if job.status in ("completed", "completed_with_errors", "failed", "cancelled"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel job in terminal status '{job.status}'",
            )

        job.status = "cancelled"
        job.error_message = "Job cancelled by user"
        job.completed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(job)

        event = CollectionJobEvent(
            collection_job_id=job.id,
            event_type="cancelled",
            message="Collection job cancelled by user",
        )
        self.db.add(event)
        await self.db.commit()

        return CollectionJobResponse.model_validate(job)

    async def retry_job(self, job_id: str, user_id: str) -> CollectionJobResponse:
        job = await self.job_repo.get_by_id(job_id, user_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection job not found",
            )

        if job.status not in ("failed", "completed_with_errors", "cancelled"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only failed, completed_with_errors, or cancelled jobs can be retried. Current status: '{job.status}'",
            )

        job.status = "queued"
        job.current_stage = "initializing"
        job.progress_percentage = 0
        job.error_message = None
        job.retry_count += 1
        job.started_at = None
        job.completed_at = None
        await self.db.commit()
        await self.db.refresh(job)

        event = CollectionJobEvent(
            collection_job_id=job.id,
            event_type="info",
            message=f"Collection job retry #{job.retry_count} queued",
        )
        self.db.add(event)
        await self.db.commit()

        dispatch_collection_job(job.id)
        return CollectionJobResponse.model_validate(job)

    async def get_job_events(
        self, job_id: str, user_id: str
    ) -> CollectionJobEventListResponse:
        events = await self.job_repo.get_events(job_id, user_id)
        return CollectionJobEventListResponse(
            items=[CollectionJobEventResponse.model_validate(e) for e in events],
            total=len(events),
        )

    async def list_dataset_records(
        self,
        dataset_id: str,
        user_id: str,
        page: int = 1,
        size: int = 50,
        search: Optional[str] = None,
        validation_status: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ) -> DatasetRecordListResponse:
        records, total = await self.record_repo.list_records(
            dataset_id=dataset_id,
            user_id=user_id,
            page=page,
            size=size,
            search=search,
            validation_status=validation_status,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        pages = (total + size - 1) // size if total > 0 else 1
        return DatasetRecordListResponse(
            items=[DatasetRecordResponse.model_validate(r) for r in records],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def get_record_provenance(
        self, record_id: str, user_id: str
    ) -> List[RecordSourceResponse]:
        provenances = await self.record_repo.get_record_provenance(record_id, user_id)
        return [RecordSourceResponse.model_validate(p) for p in provenances]

    async def list_dataset_sources(
        self,
        dataset_id: str,
        user_id: str,
        page: int = 1,
        size: int = 50,
        domain: Optional[str] = None,
        retrieval_status: Optional[str] = None,
    ) -> DataSourceListResponse:
        sources, total = await self.record_repo.list_sources(
            dataset_id=dataset_id,
            user_id=user_id,
            page=page,
            size=size,
            domain=domain,
            retrieval_status=retrieval_status,
        )
        pages = (total + size - 1) // size if total > 0 else 1
        return DataSourceListResponse(
            items=[DataSourceResponse.model_validate(s) for s in sources],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def get_dataset_overview_stats(
        self, dataset_id: str, user_id: str
    ) -> DatasetOverviewStats:
        stats = await self.record_repo.get_dataset_overview_stats(dataset_id, user_id)
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found",
            )
        return DatasetOverviewStats(**stats)

    async def export_dataset(
        self, dataset_id: str, user_id: str, export_format: str = "json"
    ) -> Tuple[str, str, str]:
        """
        Exports dataset records to CSV or JSON format.
        Returns: (content_str, media_type, filename)
        """
        records, _ = await self.record_repo.list_records(
            dataset_id=dataset_id, user_id=user_id, page=1, size=5000
        )
        if not records:
            # Check dataset exists
            ds_q = select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == user_id)
            ds_res = await self.db.execute(ds_q)
            dataset = ds_res.scalar_one_or_none()
            if not dataset:
                raise HTTPException(status_code=404, detail="Dataset not found")

        # Fetch dataset details for filename
        ds_q = select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == user_id)
        ds_res = await self.db.execute(ds_q)
        dataset = ds_res.scalar_one()
        clean_name = "".join(c for c in dataset.name if c.isalnum() or c in ("-", "_")).rstrip()

        if export_format.lower() == "csv":
            output = io.StringIO()
            # Extract header keys from records
            all_keys = set()
            for r in records:
                all_keys.update(r.record_data.keys())
            headers = sorted(list(all_keys))

            writer = csv.DictWriter(output, fieldnames=headers)
            writer.writeheader()
            for r in records:
                writer.writerow(r.record_data)

            content = output.getvalue()
            filename = f"{clean_name}_{dataset.id[:8]}.csv"
            return content, "text/csv", filename
        else:
            export_data = [
                {
                    "id": r.id,
                    "validation_status": r.validation_status,
                    "data": r.record_data,
                    "normalized": r.normalized_data,
                    "created_at": r.created_at.isoformat(),
                }
                for r in records
            ]
            content = json.dumps(export_data, indent=2, default=str)
            filename = f"{clean_name}_{dataset.id[:8]}.json"
            return content, "application/json", filename
