from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from app.models.project import Project
from app.models.dataset import Dataset
from app.models.workflow import WorkflowRun
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db: AsyncSession):
        super().__init__(Project, db)

    async def get_user_project(
        self, project_id: str, user_id: str
    ) -> Optional[Project]:
        query = select(Project).where(
            Project.id == project_id, Project.user_id == user_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_user_projects(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Tuple[List[Project], int]:
        query = select(Project).where(Project.user_id == user_id)

        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Project.name.ilike(search_pattern),
                    Project.description.ilike(search_pattern),
                )
            )

        if status:
            query = query.where(Project.status == status)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Ordering and pagination
        query = query.order_by(desc(Project.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_project_counts(self, project_id: str) -> Tuple[int, int]:
        d_count_query = select(func.count(Dataset.id)).where(
            Dataset.project_id == project_id
        )
        w_count_query = select(func.count(WorkflowRun.id)).where(
            WorkflowRun.project_id == project_id
        )

        d_res = await self.db.execute(d_count_query)
        w_res = await self.db.execute(w_count_query)

        return d_res.scalar_one() or 0, w_res.scalar_one() or 0
