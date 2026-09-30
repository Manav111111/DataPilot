import copy
import hashlib
import json
import uuid
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.dataset import Dataset
from app.models.dataset_record import DatasetRecord
from app.models.dataset_version import DatasetVersion
from app.models.dataset_chart import DatasetChart
from app.models.dataset_export import DatasetExport
from app.repositories.dataset_repo import DatasetRepository
from app.repositories.dataset_management_repo import DatasetManagementRepository
from app.datasets.profiling.profiler import DatasetProfiler
from app.datasets.cleaning.cleaning_service import DatasetCleaningService
from app.datasets.transformations.transformer import DatasetTransformer
from app.datasets.duplicates.dedup_resolver import DuplicateResolver
from app.datasets.analytics.analytics_service import DatasetAnalyticsService
from app.datasets.comparison.comparator import DatasetComparator
from app.datasets.export.export_service import DatasetExportService


class DatasetManagementService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.dataset_repo = DatasetRepository(session)
        self.mgmt_repo = DatasetManagementRepository(session)

    async def _verify_dataset_ownership(
        self, dataset_id: uuid.UUID, user_id: uuid.UUID
    ) -> Dataset:
        dataset = await self.dataset_repo.get_user_dataset(str(dataset_id), str(user_id))
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found or access denied.",
            )
        return dataset

    # ----------------------------------------------------
    # 1. Dataset Profiling & Quality
    # ----------------------------------------------------
    async def profile_dataset(
        self, dataset_id: uuid.UUID, user_id: uuid.UUID
    ) -> Dict[str, Any]:
        dataset = await self._verify_dataset_ownership(dataset_id, user_id)
        db_records = await self.mgmt_repo.get_all_dataset_records(dataset_id)
        sources_count = await self.mgmt_repo.count_dataset_sources(dataset_id)
        provenance_count = await self.mgmt_repo.count_provenance_links(dataset_id)

        records_dicts = [
            {
                "id": str(r.id),
                "record_data": r.record_data,
                "normalized_data": r.normalized_data,
                "record_hash": r.record_hash,
                "validation_status": r.validation_status,
                "source_count": r.source_count,
            }
            for r in db_records
        ]

        from app.models.collection_job import CollectionJob
        from app.models.plan import CollectionPlan
        from sqlalchemy import select

        schema_fields = []
        job_stmt = (
            select(CollectionJob)
            .where(CollectionJob.dataset_id == str(dataset_id))
            .order_by(CollectionJob.created_at.desc())
            .limit(1)
        )
        job_res = await self.session.execute(job_stmt)
        latest_job = job_res.scalar_one_or_none()
        if latest_job and latest_job.plan_id:
            plan_stmt = select(CollectionPlan).where(CollectionPlan.id == str(latest_job.plan_id))
            plan_res = await self.session.execute(plan_stmt)
            plan_obj = plan_res.scalar_one_or_none()
            if plan_obj and plan_obj.plan_data:
                p_data = plan_obj.plan_data if isinstance(plan_obj.plan_data, dict) else {}
                schema_fields = p_data.get("fields") or p_data.get("schema", {}).get("fields") or []

        dataset_meta = {
            "created_at": dataset.created_at.isoformat() if dataset.created_at else None,
            "updated_at": dataset.updated_at.isoformat() if dataset.updated_at else None,
        }

        profile_results = DatasetProfiler.profile_dataset(
            records=records_dicts,
            schema_fields=schema_fields,
            sources_count=sources_count,
            provenance_count=provenance_count,
            dataset_meta=dataset_meta,
        )

        # Save to database
        quality_info = profile_results["quality"]
        await self.mgmt_repo.create_quality_report(
            dataset_id=dataset_id,
            quality_score=quality_info["overall_score"],
            dimension_scores=quality_info["dimension_scores"],
            report_data=profile_results,
            scoring_method_version=quality_info["scoring_method_version"],
        )

        return {
            "dataset_id": dataset.id,
            "dataset_name": dataset.name,
            "overview": profile_results["overview"],
            "columns": profile_results["columns"],
            "quality": profile_results["quality"],
            "profiled_at": profile_results["profiled_at"],
        }

    async def get_latest_quality_report(
        self, dataset_id: uuid.UUID, user_id: uuid.UUID
    ) -> Dict[str, Any]:
        await self._verify_dataset_ownership(dataset_id, user_id)
        report = await self.mgmt_repo.get_latest_quality_report(dataset_id)
        if not report:
            # Generate on the fly
            return await self.profile_dataset(dataset_id, user_id)

        return {
            "id": report.id,
            "dataset_id": report.dataset_id,
            "quality_score": report.quality_score,
            "dimension_scores": report.dimension_scores,
            "report_data": report.report_data,
            "scoring_method_version": report.scoring_method_version,
            "created_at": report.created_at,
        }

    # ----------------------------------------------------
    # 2. Data Cleaning & Normalization
    # ----------------------------------------------------
    async def clean_preview(
        self,
        dataset_id: uuid.UUID,
        user_id: uuid.UUID,
        operation_type: str,
        configuration: Dict[str, Any],
    ) -> Dict[str, Any]:
        await self._verify_dataset_ownership(dataset_id, user_id)
        db_records = await self.mgmt_repo.get_all_dataset_records(dataset_id)
        records_dicts = [
            {
                "id": str(r.id),
                "record_data": r.record_data,
                "normalized_data": r.normalized_data,
                "record_hash": r.record_hash,
                "validation_status": r.validation_status,
                "source_count": r.source_count,
            }
            for r in db_records
        ]
        return DatasetCleaningService.preview_clean(
            records=records_dicts,
            operation_type=operation_type,
            configuration=configuration,
        )

    async def clean_apply(
        self,
        dataset_id: uuid.UUID,
        user_id: uuid.UUID,
        operation_type: str,
        configuration: Dict[str, Any],
        create_version: bool = True,
        change_summary: Optional[str] = None,
    ) -> Dict[str, Any]:
        dataset = await self._verify_dataset_ownership(dataset_id, user_id)
        db_records = await self.mgmt_repo.get_all_dataset_records(dataset_id)
        records_dicts = [
            {
                "id": str(r.id),
                "record_data": r.record_data,
                "normalized_data": r.normalized_data,
                "record_hash": r.record_hash,
                "validation_status": r.validation_status,
                "source_count": r.source_count,
            }
            for r in db_records
        ]

        # Snapshot prior version if requested
        if create_version:
            await self.mgmt_repo.create_version_snapshot(
                dataset_id=dataset_id,
                change_type="cleaning",
                change_summary=change_summary or f"Applied cleaning: {operation_type.replace('_', ' ').title()}",
                schema_snapshot={"fields": list(records_dicts[0]["record_data"].keys()) if records_dicts else []},
                record_count=len(records_dicts),
                snapshot_data=records_dicts,
                created_by=user_id,
            )

        clean_results = DatasetCleaningService.apply_clean(
            records=records_dicts,
            operation_type=operation_type,
            configuration=configuration,
        )

        cleaned_records = clean_results["cleaned_records"]
        deleted_ids = [uuid.UUID(rid) for rid in clean_results["deleted_record_ids"]]
        records_affected = clean_results["records_affected"]

        # Apply updates to database
        if deleted_ids:
            await self.mgmt_repo.bulk_delete_records(deleted_ids)

        update_payloads = [
            {
                "id": uuid.UUID(r["id"]),
                "record_data": r["record_data"],
                "normalized_data": r["normalized_data"],
                "record_hash": r["record_hash"],
                "source_count": r.get("source_count", 1),
                "validation_status": r.get("validation_status", "valid"),
            }
            for r in cleaned_records
            if uuid.UUID(r["id"]) not in deleted_ids
        ]
        if update_payloads:
            await self.mgmt_repo.bulk_update_records(update_payloads)

        # Record Transformation
        transform = await self.mgmt_repo.create_transformation(
            dataset_id=dataset_id,
            operation_type=f"clean_{operation_type}",
            configuration=configuration,
            records_affected=records_affected,
            initiated_by=user_id,
        )

        # Update dataset row count
        dataset.row_count = len(cleaned_records)
        await self.session.commit()

        # Re-profile dataset
        await self.profile_dataset(dataset_id, user_id)

        return {
            "message": f"Successfully applied cleaning operation '{operation_type}'.",
            "records_affected": records_affected,
            "transformation_id": transform.id,
            "remaining_record_count": len(cleaned_records),
        }

    # ----------------------------------------------------
    # 3. Transformations & Derived Columns
    # ----------------------------------------------------
    async def transform_preview(
        self,
        dataset_id: uuid.UUID,
        user_id: uuid.UUID,
        operation_type: str,
        configuration: Dict[str, Any],
    ) -> Dict[str, Any]:
        await self._verify_dataset_ownership(dataset_id, user_id)
        db_records = await self.mgmt_repo.get_all_dataset_records(dataset_id)
        records_dicts = [
            {
                "id": str(r.id),
                "record_data": r.record_data,
                "normalized_data": r.normalized_data,
                "record_hash": r.record_hash,
                "validation_status": r.validation_status,
                "source_count": r.source_count,
            }
            for r in db_records
        ]
        return DatasetTransformer.preview_transformation(
            records=records_dicts,
            operation_type=operation_type,
            configuration=configuration,
        )

    async def transform_apply(
        self,
        dataset_id: uuid.UUID,
        user_id: uuid.UUID,
        operation_type: str,
        configuration: Dict[str, Any],
        create_version: bool = True,
        change_summary: Optional[str] = None,
    ) -> Dict[str, Any]:
        dataset = await self._verify_dataset_ownership(dataset_id, user_id)
        db_records = await self.mgmt_repo.get_all_dataset_records(dataset_id)
        records_dicts = [
            {
                "id": str(r.id),
                "record_data": r.record_data,
                "normalized_data": r.normalized_data,
                "record_hash": r.record_hash,
                "validation_status": r.validation_status,
                "source_count": r.source_count,
            }
            for r in db_records
        ]

        if create_version:
            await self.mgmt_repo.create_version_snapshot(
                dataset_id=dataset_id,
                change_type="transformation",
                change_summary=change_summary or f"Applied transformation: {operation_type.replace('_', ' ').title()}",
                schema_snapshot={"fields": list(records_dicts[0]["record_data"].keys()) if records_dicts else []},
                record_count=len(records_dicts),
                snapshot_data=records_dicts,
                created_by=user_id,
            )

        res = DatasetTransformer.apply_transformation(
            records=records_dicts,
            operation_type=operation_type,
            configuration=configuration,
        )

        transformed_records = res["transformed_records"]
        deleted_ids = [uuid.UUID(rid) for rid in res["deleted_record_ids"]]
        records_affected = res["records_affected"]

        if deleted_ids:
            await self.mgmt_repo.bulk_delete_records(deleted_ids)

        update_payloads = [
            {
                "id": uuid.UUID(r["id"]),
                "record_data": r["record_data"],
                "normalized_data": r["normalized_data"],
                "record_hash": r["record_hash"],
                "source_count": r.get("source_count", 1),
                "validation_status": r.get("validation_status", "valid"),
            }
            for r in transformed_records
            if uuid.UUID(r["id"]) not in deleted_ids
        ]
        if update_payloads:
            await self.mgmt_repo.bulk_update_records(update_payloads)

        transform = await self.mgmt_repo.create_transformation(
            dataset_id=dataset_id,
            operation_type=operation_type,
            configuration=configuration,
            records_affected=records_affected,
            initiated_by=user_id,
        )

        dataset.row_count = len(transformed_records)
        await self.session.commit()

        # Re-profile dataset
        await self.profile_dataset(dataset_id, user_id)

        return {
            "message": f"Successfully applied transformation '{operation_type}'.",
            "records_affected": records_affected,
            "transformation_id": transform.id,
            "remaining_record_count": len(transformed_records),
        }

    async def list_transformations(
        self, dataset_id: uuid.UUID, user_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        await self._verify_dataset_ownership(dataset_id, user_id)
        transforms = await self.mgmt_repo.list_transformations(dataset_id)
        return [
            {
                "id": t.id,
                "dataset_id": t.dataset_id,
                "operation_type": t.operation_type,
                "configuration": t.configuration,
                "status": t.status,
                "records_affected": t.records_affected,
                "created_at": t.created_at,
                "completed_at": t.completed_at,
            }
            for t in transforms
        ]

    # ----------------------------------------------------
    # 4. Duplicate Groups & Merging
    # ----------------------------------------------------
    async def get_duplicate_groups(
        self,
        dataset_id: uuid.UUID,
        user_id: uuid.UUID,
        key_fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        await self._verify_dataset_ownership(dataset_id, user_id)
        db_records = await self.mgmt_repo.get_all_dataset_records(dataset_id)
        records_dicts = [
            {
                "id": str(r.id),
                "record_data": r.record_data,
                "normalized_data": r.normalized_data,
                "record_hash": r.record_hash,
                "validation_status": r.validation_status,
                "source_count": r.source_count,
            }
            for r in db_records
        ]
        return DuplicateResolver.find_duplicate_groups(records_dicts, key_fields)

    async def merge_duplicates(
        self,
        dataset_id: uuid.UUID,
        user_id: uuid.UUID,
        retained_record_id: uuid.UUID,
        merged_record_ids: List[uuid.UUID],
        field_overrides: Optional[Dict[str, Any]] = None,
        create_version: bool = True,
    ) -> Dict[str, Any]:
        dataset = await self._verify_dataset_ownership(dataset_id, user_id)
        db_records = await self.mgmt_repo.get_all_dataset_records(dataset_id)
        records_by_id = {str(r.id): r for r in db_records}

        retained_r = records_by_id.get(str(retained_record_id))
        if not retained_r:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Retained record not found.")

        merged_records = []
        for mid in merged_record_ids:
            mr = records_by_id.get(str(mid))
            if mr:
                merged_records.append({
                    "id": str(mr.id),
                    "record_data": mr.record_data,
                    "source_count": mr.source_count,
                })

        if not merged_records:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid records specified to merge.")

        # Version snapshot
        if create_version:
            records_dicts = [
                {
                    "id": str(r.id),
                    "record_data": r.record_data,
                    "normalized_data": r.normalized_data,
                    "record_hash": r.record_hash,
                    "validation_status": r.validation_status,
                    "source_count": r.source_count,
                }
                for r in db_records
            ]
            await self.mgmt_repo.create_version_snapshot(
                dataset_id=dataset_id,
                change_type="merge",
                change_summary=f"Merged {len(merged_record_ids)} duplicate records into record {str(retained_record_id)[:8]}",
                schema_snapshot={"fields": list(retained_r.record_data.keys()) if retained_r.record_data else []},
                record_count=len(db_records),
                snapshot_data=records_dicts,
                created_by=user_id,
            )

        # Merge data logic
        merged_dict = DuplicateResolver.prepare_merged_record(
            retained_record={
                "id": str(retained_r.id),
                "record_data": retained_r.record_data,
                "source_count": retained_r.source_count,
            },
            merged_records=merged_records,
            field_overrides=field_overrides,
        )

        # 1. Update retained record
        retained_r.record_data = merged_dict["record_data"]
        retained_r.normalized_data = merged_dict["normalized_data"]
        retained_r.record_hash = merged_dict["record_hash"]
        retained_r.source_count = merged_dict["source_count"]

        # 2. Relink source provenance to retained record
        await self.mgmt_repo.relink_record_sources(merged_record_ids, retained_record_id)

        # 3. Delete merged records
        await self.mgmt_repo.bulk_delete_records(merged_record_ids)

        # 4. Record Merge History
        await self.mgmt_repo.record_merge_history(
            dataset_id=dataset_id,
            retained_record_id=retained_record_id,
            merged_record_ids=[str(mid) for mid in merged_record_ids],
            merge_configuration={
                "field_overrides": field_overrides or {},
                "original_retained_data": retained_r.record_data,
            },
            created_by=user_id,
        )

        dataset.row_count = max(0, len(db_records) - len(merged_record_ids))
        await self.session.commit()

        # Re-profile dataset
        await self.profile_dataset(dataset_id, user_id)

        return {
            "message": f"Successfully merged {len(merged_record_ids)} records into retained record.",
            "retained_record_id": retained_record_id,
            "total_source_count": retained_r.source_count,
            "remaining_record_count": dataset.row_count,
        }

    # ----------------------------------------------------
    # 5. Record Editing (Inline & Bulk)
    # ----------------------------------------------------
    async def update_record(
        self,
        record_id: uuid.UUID,
        user_id: uuid.UUID,
        record_data: Dict[str, Any],
        validation_status: Optional[str] = None,
    ) -> Dict[str, Any]:
        rec_stmt = (
            self.session.query(DatasetRecord)
            if hasattr(self.session, "query")
            else None
        )
        # Using select
        from sqlalchemy import select
        stmt = select(DatasetRecord).join(Dataset).where(DatasetRecord.id == record_id, Dataset.user_id == user_id)
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found or access denied.")

        record.record_data = record_data
        record.normalized_data = copy.deepcopy(record_data)
        record.record_hash = hashlib.sha256(json.dumps(record_data, sort_keys=True).encode()).hexdigest()
        if validation_status:
            record.validation_status = validation_status

        await self.session.commit()
        await self.session.refresh(record)

        return {
            "id": record.id,
            "dataset_id": record.dataset_id,
            "record_data": record.record_data,
            "validation_status": record.validation_status,
            "record_hash": record.record_hash,
            "source_count": record.source_count,
        }

    async def delete_record(
        self, record_id: uuid.UUID, user_id: uuid.UUID
    ) -> Dict[str, Any]:
        from sqlalchemy import select
        stmt = select(DatasetRecord).join(Dataset).where(DatasetRecord.id == record_id, Dataset.user_id == user_id)
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found.")

        dataset_id = record.dataset_id
        await self.session.delete(record)
        await self.session.commit()

        # Update dataset row count
        dataset = await self.dataset_repo.get_user_dataset(str(dataset_id), str(user_id))
        if dataset:
            dataset.row_count = max(0, dataset.row_count - 1)
            await self.session.commit()

        return {"message": "Record deleted successfully.", "record_id": record_id}

    async def bulk_update_records(
        self,
        dataset_id: uuid.UUID,
        user_id: uuid.UUID,
        record_ids: List[uuid.UUID],
        updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        await self._verify_dataset_ownership(dataset_id, user_id)
        db_records = await self.mgmt_repo.get_all_dataset_records(dataset_id)
        id_set = set(record_ids)
        affected_count = 0

        for r in db_records:
            if r.id in id_set:
                data = copy.deepcopy(r.record_data or {})
                for k, v in updates.items():
                    data[k] = v
                r.record_data = data
                r.normalized_data = copy.deepcopy(data)
                r.record_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
                affected_count += 1

        await self.session.commit()
        return {"message": f"Updated {affected_count} records.", "records_affected": affected_count}

    async def bulk_delete_records(
        self,
        dataset_id: uuid.UUID,
        user_id: uuid.UUID,
        record_ids: List[uuid.UUID],
    ) -> Dict[str, Any]:
        dataset = await self._verify_dataset_ownership(dataset_id, user_id)
        await self.mgmt_repo.bulk_delete_records(record_ids)
        dataset.row_count = max(0, dataset.row_count - len(record_ids))
        await self.session.commit()
        return {"message": f"Deleted {len(record_ids)} records.", "records_deleted": len(record_ids)}

    # ----------------------------------------------------
    # 6. Analytics & Dynamic Charts
    # ----------------------------------------------------
    async def get_analytics_overview(
        self, dataset_id: uuid.UUID, user_id: uuid.UUID
    ) -> Dict[str, Any]:
        await self._verify_dataset_ownership(dataset_id, user_id)
        return await self.profile_dataset(dataset_id, user_id)

    async def get_field_distributions(
        self,
        dataset_id: uuid.UUID,
        user_id: uuid.UUID,
        field_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        await self._verify_dataset_ownership(dataset_id, user_id)
        db_records = await self.mgmt_repo.get_all_dataset_records(dataset_id)
        records_dicts = [
            {
                "id": str(r.id),
                "record_data": r.record_data,
            }
            for r in db_records
        ]
        return DatasetAnalyticsService.get_field_distributions(records_dicts, field_names)

    async def create_chart(
        self,
        dataset_id: uuid.UUID,
        user_id: uuid.UUID,
        chart_name: str,
        chart_type: str,
        configuration: Dict[str, Any],
    ) -> Dict[str, Any]:
        await self._verify_dataset_ownership(dataset_id, user_id)
        chart = await self.mgmt_repo.create_chart(
            dataset_id=dataset_id,
            chart_name=chart_name,
            chart_type=chart_type,
            configuration=configuration,
            created_by=user_id,
        )
        return {
            "id": chart.id,
            "dataset_id": chart.dataset_id,
            "chart_name": chart.chart_name,
            "chart_type": chart.chart_type,
            "configuration": chart.configuration,
            "created_at": chart.created_at,
            "updated_at": chart.updated_at,
        }

    async def list_charts(
        self, dataset_id: uuid.UUID, user_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        await self._verify_dataset_ownership(dataset_id, user_id)
        charts = await self.mgmt_repo.list_charts(dataset_id)
        db_records = await self.mgmt_repo.get_all_dataset_records(dataset_id)
        records_dicts = [{"record_data": r.record_data} for r in db_records]

        res = []
        for c in charts:
            computed = DatasetAnalyticsService.compute_chart_data(
                records=records_dicts,
                chart_type=c.chart_type,
                configuration={**c.configuration, "chart_name": c.chart_name},
            )
            res.append({
                "id": c.id,
                "dataset_id": c.dataset_id,
                "chart_name": c.chart_name,
                "chart_type": c.chart_type,
                "configuration": c.configuration,
                "computed_data": computed.get("data", []),
                "created_at": c.created_at,
                "updated_at": c.updated_at,
            })
        return res

    async def update_chart(
        self,
        chart_id: uuid.UUID,
        user_id: uuid.UUID,
        chart_name: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        chart = await self.mgmt_repo.get_chart(chart_id)
        if not chart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chart not found.")
        await self._verify_dataset_ownership(chart.dataset_id, user_id)
        updated = await self.mgmt_repo.update_chart(chart, chart_name, configuration)
        return {
            "id": updated.id,
            "dataset_id": updated.dataset_id,
            "chart_name": updated.chart_name,
            "chart_type": updated.chart_type,
            "configuration": updated.configuration,
            "created_at": updated.created_at,
            "updated_at": updated.updated_at,
        }

    async def delete_chart(self, chart_id: uuid.UUID, user_id: uuid.UUID) -> Dict[str, Any]:
        chart = await self.mgmt_repo.get_chart(chart_id)
        if not chart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chart not found.")
        await self._verify_dataset_ownership(chart.dataset_id, user_id)
        await self.mgmt_repo.delete_chart(chart_id)
        return {"message": "Chart deleted successfully."}

    # ----------------------------------------------------
    # 7. Dataset Comparison
    # ----------------------------------------------------
    async def compare_datasets(
        self,
        user_id: uuid.UUID,
        dataset_id_a: uuid.UUID,
        dataset_id_b: uuid.UUID,
        matching_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        dataset_a = await self._verify_dataset_ownership(dataset_id_a, user_id)
        dataset_b = await self._verify_dataset_ownership(dataset_id_b, user_id)

        records_a = await self.mgmt_repo.get_all_dataset_records(dataset_id_a)
        records_b = await self.mgmt_repo.get_all_dataset_records(dataset_id_b)

        report_a = await self.mgmt_repo.get_latest_quality_report(dataset_id_a)
        report_b = await self.mgmt_repo.get_latest_quality_report(dataset_id_b)

        qa = report_a.quality_score if report_a else 0.0
        qb = report_b.quality_score if report_b else 0.0

        return DatasetComparator.compare_datasets(
            dataset_a_meta={"id": dataset_a.id, "name": dataset_a.name, "quality_score": qa},
            records_a=[{"id": str(r.id), "record_data": r.record_data, "record_hash": r.record_hash} for r in records_a],
            dataset_b_meta={"id": dataset_b.id, "name": dataset_b.name, "quality_score": qb},
            records_b=[{"id": str(r.id), "record_data": r.record_data, "record_hash": r.record_hash} for r in records_b],
            matching_key=matching_key,
        )

    # ----------------------------------------------------
    # 8. Export Center
    # ----------------------------------------------------
    async def create_export(
        self,
        dataset_id: uuid.UUID,
        user_id: uuid.UUID,
        export_format: str,
        columns: Optional[List[str]] = None,
        include_provenance: bool = True,
        include_warnings: bool = False,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        dataset = await self._verify_dataset_ownership(dataset_id, user_id)
        db_records = await self.mgmt_repo.get_all_dataset_records(dataset_id)
        report = await self.mgmt_repo.get_latest_quality_report(dataset_id)

        records_dicts = [
            {
                "id": str(r.id),
                "record_data": r.record_data,
                "validation_status": r.validation_status,
                "source_count": r.source_count,
            }
            for r in db_records
        ]

        # Apply simple filters if specified
        if filters:
            if filters.get("validation_status"):
                records_dicts = [r for r in records_dicts if r["validation_status"] == filters["validation_status"]]

        export_res = DatasetExportService.export_to_file(
            records=records_dicts,
            export_format=export_format,
            dataset_id=str(dataset_id),
            dataset_name=dataset.name,
            columns=columns,
            quality_summary={
                "overall_score": report.quality_score if report else 0.0,
                "dimension_scores": report.dimension_scores if report else {},
            },
            include_provenance=include_provenance,
            include_warnings=include_warnings,
        )

        # Record in database
        exp_record = await self.mgmt_repo.create_export(
            dataset_id=dataset_id,
            user_id=user_id,
            export_format=export_format,
            export_configuration={
                "columns": columns,
                "include_provenance": include_provenance,
                "include_warnings": include_warnings,
                "filters": filters or {},
            },
            status="completed",
            file_reference=export_res["file_path"],
            file_size_bytes=export_res["file_size_bytes"],
            record_count=export_res["record_count"],
        )

        return {
            "id": exp_record.id,
            "dataset_id": dataset_id,
            "format": export_format,
            "export_configuration": exp_record.export_configuration,
            "status": "completed",
            "file_reference": exp_record.file_reference,
            "file_size_bytes": exp_record.file_size_bytes,
            "record_count": exp_record.record_count,
            "download_url": f"/api/v1/exports/{exp_record.id}/download",
            "created_at": exp_record.created_at,
            "completed_at": exp_record.completed_at,
        }

    async def get_export(self, export_id: uuid.UUID, user_id: uuid.UUID) -> Dict[str, Any]:
        exp = await self.mgmt_repo.get_export(export_id)
        if not exp or exp.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export not found.")
        return {
            "id": exp.id,
            "dataset_id": exp.dataset_id,
            "format": exp.format,
            "export_configuration": exp.export_configuration,
            "status": exp.status,
            "file_reference": exp.file_reference,
            "file_size_bytes": exp.file_size_bytes,
            "record_count": exp.record_count,
            "download_url": f"/api/v1/exports/{exp.id}/download",
            "created_at": exp.created_at,
            "completed_at": exp.completed_at,
        }

    async def list_exports(self, dataset_id: uuid.UUID, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        await self._verify_dataset_ownership(dataset_id, user_id)
        exports = await self.mgmt_repo.list_exports(dataset_id)
        return [
            {
                "id": e.id,
                "dataset_id": e.dataset_id,
                "format": e.format,
                "export_configuration": e.export_configuration,
                "status": e.status,
                "file_reference": e.file_reference,
                "file_size_bytes": e.file_size_bytes,
                "record_count": e.record_count,
                "download_url": f"/api/v1/exports/{e.id}/download",
                "created_at": e.created_at,
                "completed_at": e.completed_at,
            }
            for e in exports
        ]

    # ----------------------------------------------------
    # 9. Version History & Restoration
    # ----------------------------------------------------
    async def list_versions(self, dataset_id: uuid.UUID, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        await self._verify_dataset_ownership(dataset_id, user_id)
        versions = await self.mgmt_repo.list_versions(dataset_id)
        return [
            {
                "id": v.id,
                "dataset_id": v.dataset_id,
                "version_number": v.version_number,
                "change_type": v.change_type,
                "change_summary": v.change_summary,
                "record_count": v.record_count,
                "schema_snapshot": v.schema_snapshot,
                "created_at": v.created_at,
            }
            for v in versions
        ]

    async def get_version(self, version_id: uuid.UUID, user_id: uuid.UUID) -> Dict[str, Any]:
        ver = await self.mgmt_repo.get_version(version_id)
        if not ver:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found.")
        await self._verify_dataset_ownership(ver.dataset_id, user_id)
        return {
            "id": ver.id,
            "dataset_id": ver.dataset_id,
            "version_number": ver.version_number,
            "change_type": ver.change_type,
            "change_summary": ver.change_summary,
            "record_count": ver.record_count,
            "schema_snapshot": ver.schema_snapshot,
            "snapshot_data": ver.snapshot_data,
            "created_at": ver.created_at,
        }

    async def restore_version(
        self,
        dataset_id: uuid.UUID,
        version_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Dict[str, Any]:
        dataset = await self._verify_dataset_ownership(dataset_id, user_id)
        ver = await self.mgmt_repo.get_version(version_id)
        if not ver or str(ver.dataset_id) != str(dataset_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found.")

        # Snapshot current state before restore
        current_records = await self.mgmt_repo.get_all_dataset_records(dataset_id)
        current_dicts = [
            {
                "id": str(r.id),
                "record_data": r.record_data,
                "normalized_data": r.normalized_data,
                "record_hash": r.record_hash,
                "validation_status": r.validation_status,
                "source_count": r.source_count,
            }
            for r in current_records
        ]
        await self.mgmt_repo.create_version_snapshot(
            dataset_id=dataset_id,
            change_type="restore_backup",
            change_summary=f"Backup snapshot before restoring Version #{ver.version_number}",
            schema_snapshot={"fields": list(current_dicts[0]["record_data"].keys()) if current_dicts else []},
            record_count=len(current_dicts),
            snapshot_data=current_dicts,
            created_by=user_id,
        )

        # Restore records from snapshot_data
        snapshot_records = ver.snapshot_data or []

        # Delete current records
        await self.mgmt_repo.bulk_delete_records([r.id for r in current_records])

        # Re-insert snapshot records
        new_db_records = []
        for s_rec in snapshot_records:
            rec_id_val = str(s_rec["id"]) if s_rec.get("id") else str(uuid.uuid4())
            rec_obj = DatasetRecord(
                id=rec_id_val,
                dataset_id=str(dataset_id),
                record_data=s_rec.get("record_data") or s_rec.get("data") or {},
                normalized_data=s_rec.get("normalized_data") or s_rec.get("record_data") or {},
                record_hash=s_rec.get("record_hash") or hashlib.sha256(json.dumps(s_rec.get("record_data", {}), sort_keys=True).encode()).hexdigest(),
                validation_status=s_rec.get("validation_status", "valid"),
                source_count=s_rec.get("source_count", 1),
            )
            self.session.add(rec_obj)

        dataset.row_count = len(snapshot_records)
        await self.session.commit()

        # Create new version tracking the restore
        new_ver = await self.mgmt_repo.create_version_snapshot(
            dataset_id=dataset_id,
            change_type="restore",
            change_summary=f"Restored dataset to Version #{ver.version_number}",
            schema_snapshot=ver.schema_snapshot,
            record_count=len(snapshot_records),
            snapshot_data=snapshot_records,
            created_by=user_id,
        )

        # Re-profile dataset
        await self.profile_dataset(dataset_id, user_id)

        return {
            "message": f"Successfully restored dataset to Version #{ver.version_number}.",
            "restored_version_number": ver.version_number,
            "record_count": len(snapshot_records),
            "new_version_id": new_ver.id,
        }
