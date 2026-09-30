import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import delete, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.dataset import Dataset
from app.models.dataset_record import DatasetRecord
from app.models.data_source import DataSource
from app.models.record_source import RecordSource
from app.models.dataset_quality_report import DatasetQualityReport
from app.models.dataset_transformation import DatasetTransformation
from app.models.dataset_version import DatasetVersion
from app.models.dataset_chart import DatasetChart
from app.models.dataset_merge_history import DatasetMergeHistory
from app.models.dataset_export import DatasetExport


class DatasetManagementRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ----------------------------------------------------
    # Quality Reports
    # ----------------------------------------------------
    async def create_quality_report(
        self,
        dataset_id: Any,
        quality_score: float,
        dimension_scores: Dict[str, Any],
        report_data: Dict[str, Any],
        version_id: Optional[Any] = None,
        scoring_method_version: str = "v1.0",
    ) -> DatasetQualityReport:
        report = DatasetQualityReport(
            dataset_id=str(dataset_id),
            version_id=str(version_id) if version_id else None,
            quality_score=quality_score,
            dimension_scores=dimension_scores,
            report_data=report_data,
            scoring_method_version=scoring_method_version,
        )
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def get_latest_quality_report(
        self, dataset_id: Any
    ) -> Optional[DatasetQualityReport]:
        stmt = (
            select(DatasetQualityReport)
            .where(DatasetQualityReport.dataset_id == str(dataset_id))
            .order_by(desc(DatasetQualityReport.created_at))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ----------------------------------------------------
    # Transformations
    # ----------------------------------------------------
    async def create_transformation(
        self,
        dataset_id: Any,
        operation_type: str,
        configuration: Dict[str, Any],
        records_affected: int,
        initiated_by: Optional[Any] = None,
        status: str = "completed",
    ) -> DatasetTransformation:
        transform = DatasetTransformation(
            dataset_id=str(dataset_id),
            operation_type=operation_type,
            configuration=configuration,
            records_affected=records_affected,
            initiated_by=str(initiated_by) if initiated_by else None,
            status=status,
            completed_at=datetime.now(timezone.utc),
        )
        self.session.add(transform)
        await self.session.commit()
        await self.session.refresh(transform)
        return transform

    async def list_transformations(
        self, dataset_id: Any, limit: int = 50
    ) -> List[DatasetTransformation]:
        stmt = (
            select(DatasetTransformation)
            .where(DatasetTransformation.dataset_id == str(dataset_id))
            .order_by(desc(DatasetTransformation.created_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ----------------------------------------------------
    # Versions
    # ----------------------------------------------------
    async def create_version_snapshot(
        self,
        dataset_id: Any,
        change_type: str,
        change_summary: str,
        schema_snapshot: Dict[str, Any],
        record_count: int,
        snapshot_data: List[Dict[str, Any]],
        created_by: Optional[Any] = None,
    ) -> DatasetVersion:
        # Determine next version number
        count_stmt = select(func.count(DatasetVersion.id)).where(DatasetVersion.dataset_id == str(dataset_id))
        count_res = await self.session.execute(count_stmt)
        next_ver = (count_res.scalar() or 0) + 1

        ver = DatasetVersion(
            dataset_id=str(dataset_id),
            version_number=next_ver,
            change_type=change_type,
            change_summary=change_summary,
            schema_snapshot=schema_snapshot,
            record_count=record_count,
            snapshot_data=snapshot_data,
            created_by=str(created_by) if created_by else None,
        )
        self.session.add(ver)
        await self.session.commit()
        await self.session.refresh(ver)
        return ver

    async def list_versions(self, dataset_id: Any) -> List[DatasetVersion]:
        stmt = (
            select(DatasetVersion)
            .where(DatasetVersion.dataset_id == str(dataset_id))
            .order_by(desc(DatasetVersion.version_number))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_version(self, version_id: Any) -> Optional[DatasetVersion]:
        stmt = select(DatasetVersion).where(DatasetVersion.id == str(version_id))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ----------------------------------------------------
    # Charts
    # ----------------------------------------------------
    async def create_chart(
        self,
        dataset_id: Any,
        chart_name: str,
        chart_type: str,
        configuration: Dict[str, Any],
        created_by: Optional[Any] = None,
    ) -> DatasetChart:
        chart = DatasetChart(
            dataset_id=str(dataset_id),
            chart_name=chart_name,
            chart_type=chart_type,
            configuration=configuration,
            created_by=str(created_by) if created_by else None,
        )
        self.session.add(chart)
        await self.session.commit()
        await self.session.refresh(chart)
        return chart

    async def list_charts(self, dataset_id: Any) -> List[DatasetChart]:
        stmt = (
            select(DatasetChart)
            .where(DatasetChart.dataset_id == str(dataset_id))
            .order_by(desc(DatasetChart.created_at))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_chart(self, chart_id: Any) -> Optional[DatasetChart]:
        stmt = select(DatasetChart).where(DatasetChart.id == str(chart_id))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_chart(
        self,
        chart: DatasetChart,
        chart_name: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
    ) -> DatasetChart:
        if chart_name is not None:
            chart.chart_name = chart_name
        if configuration is not None:
            chart.configuration = configuration
        await self.session.commit()
        await self.session.refresh(chart)
        return chart

    async def delete_chart(self, chart_id: Any) -> bool:
        stmt = delete(DatasetChart).where(DatasetChart.id == str(chart_id))
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    # ----------------------------------------------------
    # Duplicate Merge History
    # ----------------------------------------------------
    async def record_merge_history(
        self,
        dataset_id: Any,
        retained_record_id: Any,
        merged_record_ids: List[str],
        merge_configuration: Dict[str, Any],
        created_by: Optional[Any] = None,
    ) -> DatasetMergeHistory:
        history = DatasetMergeHistory(
            dataset_id=str(dataset_id),
            retained_record_id=str(retained_record_id),
            merged_record_ids=merged_record_ids,
            merge_configuration=merge_configuration,
            created_by=str(created_by) if created_by else None,
        )
        self.session.add(history)
        await self.session.commit()
        await self.session.refresh(history)
        return history

    # ----------------------------------------------------
    # Exports
    # ----------------------------------------------------
    async def create_export(
        self,
        dataset_id: Any,
        user_id: Any,
        export_format: str,
        export_configuration: Dict[str, Any],
        status: str = "completed",
        file_reference: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
        record_count: Optional[int] = None,
    ) -> DatasetExport:
        exp = DatasetExport(
            dataset_id=str(dataset_id),
            user_id=str(user_id),
            format=export_format,
            export_configuration=export_configuration,
            status=status,
            file_reference=file_reference,
            file_size_bytes=file_size_bytes,
            record_count=record_count,
            completed_at=datetime.now(timezone.utc) if status == "completed" else None,
        )
        self.session.add(exp)
        await self.session.commit()
        await self.session.refresh(exp)
        return exp

    async def get_export(self, export_id: Any) -> Optional[DatasetExport]:
        stmt = select(DatasetExport).where(DatasetExport.id == str(export_id))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_exports(self, dataset_id: Any) -> List[DatasetExport]:
        stmt = (
            select(DatasetExport)
            .where(DatasetExport.dataset_id == str(dataset_id))
            .order_by(desc(DatasetExport.created_at))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ----------------------------------------------------
    # Record Operations & Provenance Relinking
    # ----------------------------------------------------
    async def get_all_dataset_records(
        self, dataset_id: Any
    ) -> List[DatasetRecord]:
        stmt = select(DatasetRecord).where(DatasetRecord.dataset_id == str(dataset_id))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def bulk_update_records(
        self, records_to_update: List[Dict[str, Any]]
    ):
        """
        Updates record_data, normalized_data, and record_hash in batch.
        """
        for r_dict in records_to_update:
            rec_id = str(r_dict["id"])
            stmt = (
                update(DatasetRecord)
                .where(DatasetRecord.id == rec_id)
                .values(
                    record_data=r_dict["record_data"],
                    normalized_data=r_dict.get("normalized_data", r_dict["record_data"]),
                    record_hash=r_dict["record_hash"],
                    source_count=r_dict.get("source_count", 1),
                    validation_status=r_dict.get("validation_status", "valid"),
                )
            )
            await self.session.execute(stmt)
        await self.session.commit()

    async def bulk_delete_records(self, record_ids: List[Any]):
        str_ids = [str(rid) for rid in record_ids]
        stmt = delete(DatasetRecord).where(DatasetRecord.id.in_(str_ids))
        await self.session.execute(stmt)
        await self.session.commit()

    async def relink_record_sources(
        self, from_record_ids: List[Any], to_record_id: Any
    ):
        """
        Re-assigns source links from merged records to the retained record.
        """
        str_from_ids = [str(rid) for rid in from_record_ids]
        stmt = (
            update(RecordSource)
            .where(RecordSource.dataset_record_id.in_(str_from_ids))
            .values(dataset_record_id=str(to_record_id))
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def count_dataset_sources(self, dataset_id: Any) -> int:
        stmt = select(func.count(DataSource.id)).where(DataSource.dataset_id == str(dataset_id))
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def count_provenance_links(self, dataset_id: Any) -> int:
        stmt = (
            select(func.count(RecordSource.id))
            .join(DatasetRecord, RecordSource.dataset_record_id == DatasetRecord.id)
            .where(DatasetRecord.dataset_id == str(dataset_id))
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0
