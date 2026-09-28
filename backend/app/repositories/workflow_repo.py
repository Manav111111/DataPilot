from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from app.models.workflow import WorkflowRun
from app.repositories.base import BaseRepository


class WorkflowRepository(BaseRepository[WorkflowRun]):
    def __init__(self, db: AsyncSession):
        super().__init__(WorkflowRun, db)

    async def get_user_workflow(
        self, workflow_id: str, user_id: str
    ) -> Optional[WorkflowRun]:
        query = (
            select(WorkflowRun)
            .options(selectinload(WorkflowRun.project))
            .where(WorkflowRun.id == workflow_id, WorkflowRun.user_id == user_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_user_workflows(
        self,
        user_id: str,
        project_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[WorkflowRun], int]:
        query = (
            select(WorkflowRun)
            .options(selectinload(WorkflowRun.project))
            .where(WorkflowRun.user_id == user_id)
        )

        if project_id:
            query = query.where(WorkflowRun.project_id == project_id)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(desc(WorkflowRun.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total
