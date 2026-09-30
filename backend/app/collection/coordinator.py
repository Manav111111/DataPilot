import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.collection_job import CollectionJob
from app.models.collection_job_event import CollectionJobEvent
from app.models.plan import CollectionPlan
from app.models.dataset import Dataset
from app.models.data_source import DataSource
from app.models.dataset_record import DatasetRecord
from app.models.record_source import RecordSource
from app.schemas.plan import CollectionPlanData
from app.core.config import settings
from app.collection.search.tavily_client import TavilySearchClient, SearchResult
from app.collection.extraction.firecrawl_client import FirecrawlExtractionClient, ExtractedPage
from app.collection.extraction.structured_extractor import StructuredExtractor, RawExtractedRecord
from app.collection.processing.validator import RecordValidator, ValidatedRecord
from app.collection.processing.deduplicator import DeduplicationEngine

logger = logging.getLogger(__name__)


class CollectionJobCoordinator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.search_client = TavilySearchClient()
        self.extraction_client = FirecrawlExtractionClient()
        self.structured_extractor = StructuredExtractor()

    async def log_event(
        self, job_id: str, event_type: str, message: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        event = CollectionJobEvent(
            collection_job_id=job_id,
            event_type=event_type,
            message=message,
            event_metadata=metadata,
        )
        self.db.add(event)
        await self.db.commit()

    async def check_is_cancelled(self, job_id: str) -> bool:
        stmt = select(CollectionJob.status).where(CollectionJob.id == job_id)
        result = await self.db.execute(stmt)
        status = result.scalar_one_or_none()
        return status == "cancelled"

    async def run_collection(
        self, job_id: str, max_records_override: Optional[int] = None, max_queries_override: Optional[int] = None
    ) -> CollectionJob:
        """
        Executes the full 7-stage collection workflow for an approved CollectionPlan.
        """
        # Load Job and associated Plan and Dataset
        stmt = (
            select(CollectionJob, CollectionPlan, Dataset)
            .join(CollectionPlan, CollectionJob.plan_id == CollectionPlan.id)
            .join(Dataset, CollectionJob.dataset_id == Dataset.id)
            .where(CollectionJob.id == job_id)
        )
        result = await self.db.execute(stmt)
        row = result.first()
        if not row:
            raise ValueError(f"CollectionJob {job_id} not found")

        job, plan, dataset = row
        plan_data = CollectionPlanData(**plan.plan_data)

        # STAGE 1: Initializing
        job.status = "running"
        job.current_stage = "initializing"
        job.progress_percentage = 5
        job.started_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.log_event(job.id, "stage_change", "Collection job initialized and execution started.")

        try:
            if await self.check_is_cancelled(job.id):
                return await self._handle_cancellation(job)

            # STAGE 2: Searching
            job.current_stage = "searching"
            job.progress_percentage = 15
            await self.db.commit()
            await self.log_event(job.id, "stage_change", "Executing search strategy across target sources.")

            queries = plan_data.search_queries
            max_q = max_queries_override or settings.COLLECTION_MAX_QUERIES
            queries_to_run = queries[:max_q]
            job.total_queries = len(queries_to_run)
            await self.db.commit()

            discovered_results: List[SearchResult] = []
            seen_urls = set()

            for idx, sq in enumerate(queries_to_run):
                if await self.check_is_cancelled(job.id):
                    return await self._handle_cancellation(job)

                results = await self.search_client.search(
                    query=sq.query,
                    max_results=settings.COLLECTION_MAX_RESULTS_PER_QUERY,
                    source_category=sq.category,
                )
                for r in results:
                    if r.url not in seen_urls:
                        seen_urls.add(r.url)
                        discovered_results.append(r)

                job.completed_queries = idx + 1
                job.total_sources = len(discovered_results)
                job.progress_percentage = 15 + int((idx + 1) / len(queries_to_run) * 20)
                await self.db.commit()

            await self.log_event(
                job.id,
                "info",
                f"Discovered {len(discovered_results)} unique source URLs across {len(queries_to_run)} search queries.",
            )

            # STAGE 3: Extracting
            job.current_stage = "extracting"
            job.progress_percentage = 40
            await self.db.commit()
            await self.log_event(job.id, "stage_change", "Extracting content from discovered public pages.")

            max_sources = min(len(discovered_results), settings.COLLECTION_MAX_SOURCES_PER_JOB)
            sources_to_extract = discovered_results[:max_sources]
            extracted_pages: List[ExtractedPage] = []
            data_source_records: Dict[str, DataSource] = {}

            for idx, s_res in enumerate(sources_to_extract):
                if await self.check_is_cancelled(job.id):
                    return await self._handle_cancellation(job)

                page = await self.extraction_client.extract_url(
                    url=s_res.url,
                    fallback_title=s_res.title,
                    fallback_snippet=s_res.snippet,
                )
                extracted_pages.append(page)

                ds = DataSource(
                    dataset_id=dataset.id,
                    collection_job_id=job.id,
                    source_url=page.url,
                    canonical_url=page.canonical_url,
                    domain=page.domain,
                    page_title=page.title,
                    source_type="web",
                    retrieval_status=page.status,
                    retrieved_at=page.retrieved_at,
                    content_hash=page.content_hash,
                    error_message=page.error_message,
                    search_query=s_res.search_query,
                )
                self.db.add(ds)
                data_source_records[page.url] = ds

                job.processed_sources = idx + 1
                job.progress_percentage = 40 + int((idx + 1) / len(sources_to_extract) * 20)
                await self.db.commit()

            await self.log_event(
                job.id,
                "info",
                f"Completed content extraction for {len(extracted_pages)} sources.",
            )

            # STAGE 4: Structuring records
            job.current_stage = "structuring"
            job.progress_percentage = 65
            await self.db.commit()
            await self.log_event(job.id, "stage_change", "Converting retrieved content into structured records.")

            raw_records: List[RawExtractedRecord] = []
            for page in extracted_pages:
                if await self.check_is_cancelled(job.id):
                    return await self._handle_cancellation(job)

                if page.status == "retrieved" and page.content:
                    extracted = await self.structured_extractor.extract_records_from_page(page, plan_data)
                    raw_records.extend(extracted)

            job.records_extracted = len(raw_records)
            await self.db.commit()
            await self.log_event(
                job.id,
                "info",
                f"Extracted {len(raw_records)} structured candidate records from page contents.",
            )

            # STAGE 5: Validating
            job.current_stage = "validating"
            job.progress_percentage = 75
            await self.db.commit()
            await self.log_event(job.id, "stage_change", "Validating and normalizing extracted records against schema.")

            validator = RecordValidator(plan_data)
            validated_records: List[ValidatedRecord] = []
            rejected_count = 0

            for raw_rec in raw_records:
                val_rec = validator.validate_and_normalize(raw_rec)
                if val_rec.validation_status == "invalid":
                    rejected_count += 1
                validated_records.append(val_rec)

            job.records_rejected = rejected_count
            await self.db.commit()

            # STAGE 6: Deduplicating
            job.current_stage = "deduplicating"
            job.progress_percentage = 85
            await self.db.commit()
            await self.log_event(job.id, "stage_change", "Executing deduplication and entity merging rules.")

            # Filter valid records for saving
            valid_records_to_dedup = [r for r in validated_records if r.validation_status != "invalid"]
            deduplicator = DeduplicationEngine(plan_data)
            unique_records, dup_count, merged_provenances = deduplicator.process_records(valid_records_to_dedup)

            await self.log_event(
                job.id,
                "info",
                f"Deduplication complete: {len(unique_records)} unique records identified ({dup_count} duplicates merged).",
            )

            # STAGE 7: Saving results
            job.current_stage = "saving"
            job.progress_percentage = 95
            await self.db.commit()
            await self.log_event(job.id, "stage_change", "Persisting structured records and source provenance.")

            target_limit = max_records_override or plan_data.target_record_count or settings.COLLECTION_MAX_RECORDS_PER_JOB
            records_to_save = unique_records[:target_limit]

            for rec in records_to_save:
                r_hash = deduplicator.compute_record_hash(rec.normalized_data)
                ds_record = DatasetRecord(
                    dataset_id=dataset.id,
                    record_data=rec.record_data,
                    normalized_data=rec.normalized_data,
                    record_hash=r_hash,
                    validation_status=rec.validation_status,
                    validation_errors=[e.model_dump() for e in rec.validation_errors] if rec.validation_errors else None,
                    source_count=1,
                )
                self.db.add(ds_record)
                await self.db.flush()

                # Link sources and evidence
                all_provenances = merged_provenances.get(r_hash, [])
                distinct_source_urls = set()
                for src_url, ev in all_provenances:
                    distinct_source_urls.add(src_url)
                    ds_entry = data_source_records.get(src_url)
                    if ds_entry:
                        rs = RecordSource(
                            dataset_record_id=ds_record.id,
                            data_source_id=ds_entry.id,
                            evidence_excerpt=ev.evidence_excerpt,
                            evidence_field=ev.field_name,
                        )
                        self.db.add(rs)

                ds_record.source_count = max(1, len(distinct_source_urls))

            # Update dataset metrics
            dataset.row_count = len(records_to_save)
            dataset.status = "ready"

            # Finalize Job Status
            job.records_saved = len(records_to_save)
            job.current_stage = "completed"
            job.status = "completed_with_errors" if rejected_count > 0 else "completed"
            job.progress_percentage = 100
            job.completed_at = datetime.now(timezone.utc)
            await self.db.commit()

            await self.log_event(
                job.id,
                "completed",
                f"Data collection finished successfully. Saved {len(records_to_save)} records to dataset '{dataset.name}'.",
                metadata={
                    "saved_records": len(records_to_save),
                    "rejected_records": rejected_count,
                    "sources_processed": len(extracted_pages),
                    "duplicates_merged": dup_count,
                },
            )
            return job

        except Exception as e:
            logger.exception(f"Collection job {job_id} encountered fatal error: {str(e)}")
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.log_event(job.id, "error", f"Collection job failed: {str(e)}")
            raise

    async def _handle_cancellation(self, job: CollectionJob) -> CollectionJob:
        job.status = "cancelled"
        job.error_message = "Collection job was cancelled by user."
        job.completed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.log_event(job.id, "cancelled", "Collection job was cancelled safely.")
        return job
