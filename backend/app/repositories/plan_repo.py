from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from app.models.plan import CollectionPlan
from app.repositories.base import BaseRepository


class PlanRepository(BaseRepository[CollectionPlan]):
    def __init__(self, db: AsyncSession):
        super().__init__(CollectionPlan, db)

    async def get_user_plan(
        self, plan_id: str, user_id: str
    ) -> Optional[CollectionPlan]:
        query = (
            select(CollectionPlan)
            .options(selectinload(CollectionPlan.project))
            .where(CollectionPlan.id == plan_id, CollectionPlan.user_id == user_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_project_plans(
        self,
        project_id: str,
        user_id: str,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[CollectionPlan], int]:
        query = (
            select(CollectionPlan)
            .options(selectinload(CollectionPlan.project))
            .where(
                CollectionPlan.project_id == project_id,
                CollectionPlan.user_id == user_id,
            )
        )

        if status:
            query = query.where(CollectionPlan.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        query = (
            query.order_by(desc(CollectionPlan.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total
