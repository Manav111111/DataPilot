import os
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.core.config import settings
from app.repositories.dataset_repo import DatasetRepository
from app.repositories.analysis_repo import AnalysisRepository
from app.analysis.query_planner import QueryPlanner
from app.analysis.query_validator import QueryValidator
from app.analysis.query_executor import QueryExecutor
from app.analysis.insight_service import InsightService
from app.analysis.statistics_service import StatisticsService
from app.analysis.report_service import ReportService
from app.ai.providers import get_llm_provider
from app.schemas.analysis import (
    ChatQueryResponse,
    AutoInsightsResponse,
    StatisticalAnalysisResponse,
    ReportCreateRequest,
    AnalysisReportRead,
    AnalysisSessionRead,
)

logger = logging.getLogger(__name__)


from app.models.dataset_record import DatasetRecord
from sqlalchemy import select


class AnalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.dataset_repo = DatasetRepository(db)
        self.analysis_repo = AnalysisRepository(db)
        self.planner = QueryPlanner()
        self.validator = QueryValidator()
        self.executor = QueryExecutor()
        self.llm = get_llm_provider()

    async def _load_dataset_and_df(self, dataset_id: str, user_id: str):
        dataset = await self.dataset_repo.get_user_dataset(str(dataset_id), str(user_id))
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found or access denied.",
            )

        stmt = select(DatasetRecord).where(DatasetRecord.dataset_id == str(dataset_id))
        res = await self.db.execute(stmt)
        records = list(res.scalars().all())

        raw_rows = []
        for r in records:
            data = r.record_data or r.normalized_data or {}
            raw_rows.append(data)

        df = pd.DataFrame(raw_rows) if raw_rows else pd.DataFrame()
        return dataset, df

    async def execute_chat_query(
        self, dataset_id: str, user_id: str, message: str, session_id: Optional[str] = None
    ) -> ChatQueryResponse:
        dataset, df = await self._load_dataset_and_df(dataset_id, user_id)

        # 1. Get or create session
        if session_id:
            session = await self.analysis_repo.get_session(session_id, user_id)
            if not session:
                session = await self.analysis_repo.create_session(
                    user_id=user_id,
                    project_id=dataset.project_id,
                    dataset_id=dataset_id,
                    title=message[:50] + ("..." if len(message) > 50 else ""),
                )
        else:
            session = await self.analysis_repo.create_session(
                user_id=user_id,
                project_id=dataset.project_id,
                dataset_id=dataset_id,
                title=message[:50] + ("..." if len(message) > 50 else ""),
            )

        # Save user message
        await self.analysis_repo.create_message(
            session_id=session.id,
            role="user",
            content=message,
            dataset_version=1,
        )

        if df.empty:
            empty_reply = "This dataset currently has no records to analyze. Please collect or import data first."
            empty_plan = await self.planner.plan_query(message, dataset.name, [], 0)
            exec_res = self.executor.execute(df, empty_plan)

            assistant_msg = await self.analysis_repo.create_message(
                session_id=session.id,
                role="assistant",
                content=empty_reply,
                analytical_plan=empty_plan.dict(),
                execution_result=exec_res.dict(),
                dataset_version=1,
            )

            return ChatQueryResponse(
                session_id=session.id,
                message_id=assistant_msg.id,
                reply=empty_reply,
                plan=empty_plan,
                result=exec_res,
                dataset_version=1,
            )

        # 2. Extract column metadata for planning
        columns_info = []
        for col in df.columns:
            s = df[col].dropna()
            num_s = pd.to_numeric(s, errors="coerce")
            is_num = num_s.notna().sum() > len(s) * 0.5 if len(s) > 0 else False
            col_type = "number" if is_num else "string"
            samples = s.astype(str).head(3).tolist()
            columns_info.append({"name": col, "type": col_type, "samples": samples})

        # 3. Generate Analytical Plan
        raw_plan = await self.planner.plan_query(
            user_query=message,
            dataset_name=dataset.name,
            columns_info=columns_info,
            row_count=len(df),
        )

        # 4. Validate Plan
        is_valid, err_msg, validated_plan = self.validator.validate_plan(raw_plan, df)

        # 5. Execute Plan with Pandas
        exec_result = self.executor.execute(df, validated_plan)

        # 6. Generate Natural Language Explanation
        explanation = await self._generate_explanation(
            user_query=message,
            plan=validated_plan,
            result=exec_result,
            dataset_name=dataset.name,
        )

        # 7. Persist Assistant Message
        assistant_msg = await self.analysis_repo.create_message(
            session_id=session.id,
            role="assistant",
            content=explanation,
            analytical_plan=validated_plan.model_dump(),
            execution_result=exec_result.model_dump(),
            dataset_version=1,
        )

        return ChatQueryResponse(
            session_id=session.id,
            message_id=assistant_msg.id,
            reply=explanation,
            plan=validated_plan,
            result=exec_result,
            dataset_version=1,
        )

    async def _generate_explanation(
        self, user_query: str, plan: Any, result: Any, dataset_name: str
    ) -> str:
        """
        Explains verified numbers from the computation summary without inventing figures.
        """
        table_snippet = ""
        if result.table and result.table.rows:
            sample_rows = result.table.rows[:5]
            table_snippet = f"Computed Results (First {len(sample_rows)} rows):\n"
            for r in sample_rows:
                table_snippet += f"- {r}\n"

        prompt = (
            f"Dataset: '{dataset_name}'\n"
            f"User Question: \"{user_query}\"\n"
            f"Operation Executed: {plan.operation}\n"
            f"Computation Summary: {result.computation_summary}\n"
            f"Key Metrics: {result.metrics}\n"
            f"{table_snippet}\n\n"
            "Provide a concise, professional answer to the user's question directly summarizing these exact computed numbers. "
            "Do NOT invent numbers not in the computation results. Highlight the top finding."
        )

        system_msg = (
            "You are a professional Data Intelligence Analyst explaining verified computational findings. "
            "Be direct, accurate, and concise with Markdown formatting. Do not hallucinate."
        )

        try:
            # Simple text generation via fallback explanation if mock
            if hasattr(self.llm, "generate_text"):
                return await self.llm.generate_text(prompt, system_msg)
        except Exception:
            pass

        # Robust deterministic explanation fallback
        return f"**Analysis Summary:**\n\n{result.computation_summary}"

    async def get_auto_insights(self, dataset_id: str, user_id: str) -> AutoInsightsResponse:
        dataset, df = await self._load_dataset_and_df(dataset_id, user_id)
        return InsightService.generate_auto_insights(
            df=df,
            dataset_id=dataset.id,
            dataset_name=dataset.name,
            dataset_version=1,
        )

    async def get_statistics(self, dataset_id: str, user_id: str) -> StatisticalAnalysisResponse:
        dataset, df = await self._load_dataset_and_df(dataset_id, user_id)
        return StatisticsService.calculate_statistics(
            df=df,
            dataset_id=dataset.id,
            dataset_version=1,
        )

    async def create_report(
        self, dataset_id: str, user_id: str, req: ReportCreateRequest
    ) -> AnalysisReportRead:
        dataset, df = await self._load_dataset_and_df(dataset_id, user_id)

        insights = InsightService.generate_auto_insights(
            df=df,
            dataset_id=dataset.id,
            dataset_name=dataset.name,
            dataset_version=1,
        )
        stats = StatisticsService.calculate_statistics(
            df=df,
            dataset_id=dataset.id,
            dataset_version=1,
        )

        html_content = ReportService.generate_html_report(
            dataset_name=dataset.name,
            dataset_id=dataset.id,
            dataset_version=1,
            record_count=len(df),
            report_title=req.title,
            insights_data=insights.model_dump(),
            stats_data=stats.model_dump(),
            custom_notes=req.custom_notes,
        )

        # Save HTML file locally in storage
        storage_dir = os.path.join(settings.EXPORT_STORAGE_DIR, "reports")
        os.makedirs(storage_dir, exist_ok=True)
        file_name = f"report_{dataset.id}_{int(pd.Timestamp.now('UTC').timestamp())}.html"
        file_path = os.path.join(storage_dir, file_name)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        report_data = {
            "title": req.title,
            "dataset_name": dataset.name,
            "insights_summary": len(insights.insights),
            "stats_columns_count": len(stats.descriptive_stats),
            "html_file": file_name,
        }

        report = await self.analysis_repo.create_report(
            dataset_id=dataset.id,
            user_id=user_id,
            title=req.title,
            format=req.format,
            report_data=report_data,
            file_path=file_path,
            dataset_version=1,
        )

        return AnalysisReportRead.model_validate(report)

    async def list_reports(self, dataset_id: str, user_id: str) -> List[AnalysisReportRead]:
        reports = await self.analysis_repo.list_reports(dataset_id, user_id)
        return [AnalysisReportRead.model_validate(r) for r in reports]

    async def get_report_download(self, report_id: str, user_id: str):
        report = await self.analysis_repo.get_report(report_id, user_id)
        if not report or not report.file_path or not os.path.exists(report.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report file not found or access denied.",
            )
        return report.file_path, report.title

    async def list_sessions(self, dataset_id: str, user_id: str) -> List[AnalysisSessionRead]:
        sessions = await self.analysis_repo.list_sessions_for_dataset(dataset_id, user_id)
        return [AnalysisSessionRead.model_validate(s) for s in sessions]

    async def get_session(self, session_id: str, user_id: str) -> AnalysisSessionRead:
        session = await self.analysis_repo.get_session(session_id, user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis session not found.",
            )
        return AnalysisSessionRead.model_validate(session)

    async def delete_session(self, session_id: str, user_id: str) -> bool:
        ok = await self.analysis_repo.delete_session(session_id, user_id)
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied.",
            )
        return True
