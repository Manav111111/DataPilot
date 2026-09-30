import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.analysis_session import AnalysisSession
from app.models.analysis_message import AnalysisMessage
from app.models.analysis_result import AnalysisResult
from app.models.analysis_report import AnalysisReport

logger = logging.getLogger(__name__)


class AnalysisRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # Sessions
    async def create_session(
        self, user_id: str, project_id: str, dataset_id: str, title: str = "Analysis Conversation"
    ) -> AnalysisSession:
        session = AnalysisSession(
            user_id=user_id,
            project_id=project_id,
            dataset_id=dataset_id,
            title=title,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_session(self, session_id: str, user_id: str) -> Optional[AnalysisSession]:
        stmt = (
            select(AnalysisSession)
            .where(AnalysisSession.id == session_id, AnalysisSession.user_id == user_id)
            .options(selectinload(AnalysisSession.messages))
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_sessions_for_dataset(
        self, dataset_id: str, user_id: str
    ) -> List[AnalysisSession]:
        stmt = (
            select(AnalysisSession)
            .where(AnalysisSession.dataset_id == dataset_id, AnalysisSession.user_id == user_id)
            .options(selectinload(AnalysisSession.messages))
            .order_by(desc(AnalysisSession.updated_at))
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def delete_session(self, session_id: str, user_id: str) -> bool:
        session = await self.get_session(session_id, user_id)
        if not session:
            return False
        await self.db.delete(session)
        await self.db.commit()
        return True

    # Messages
    async def create_message(
        self,
        session_id: str,
        role: str,
        content: str,
        analytical_plan: Optional[Dict[str, Any]] = None,
        execution_result: Optional[Dict[str, Any]] = None,
        dataset_version: int = 1,
    ) -> AnalysisMessage:
        msg = AnalysisMessage(
            session_id=session_id,
            role=role,
            content=content,
            analytical_plan=analytical_plan,
            execution_result=execution_result,
            dataset_version=dataset_version,
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    # Reports
    async def create_report(
        self,
        dataset_id: str,
        user_id: str,
        title: str,
        format: str,
        report_data: Dict[str, Any],
        file_path: Optional[str] = None,
        dataset_version: int = 1,
    ) -> AnalysisReport:
        report = AnalysisReport(
            dataset_id=dataset_id,
            user_id=user_id,
            title=title,
            format=format,
            report_data=report_data,
            file_path=file_path,
            dataset_version=dataset_version,
        )
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def list_reports(self, dataset_id: str, user_id: str) -> List[AnalysisReport]:
        stmt = (
            select(AnalysisReport)
            .where(AnalysisReport.dataset_id == dataset_id, AnalysisReport.user_id == user_id)
            .order_by(desc(AnalysisReport.created_at))
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_report(self, report_id: str, user_id: str) -> Optional[AnalysisReport]:
        stmt = select(AnalysisReport).where(
            AnalysisReport.id == report_id, AnalysisReport.user_id == user_id
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()
