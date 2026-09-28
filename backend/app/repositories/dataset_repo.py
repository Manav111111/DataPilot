from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import selectinload
from app.models.dataset import Dataset
from app.models.project import Project
from app.repositories.base import BaseRepository


class DatasetRepository(BaseRepository[Dataset]):
    def __init__(self, db: AsyncSession):
        super().__init__(Dataset, db)

    async def get_user_dataset(
        self, dataset_id: str, user_id: str
    ) -> Optional[Dataset]:
        query = (
            select(Dataset)
            .options(selectinload(Dataset.project))
            .where(Dataset.id == dataset_id, Dataset.user_id == user_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_user_datasets(
        self,
        user_id: str,
        project_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Tuple[List[Dataset], int]:
        query = (
            select(Dataset)
            .options(selectinload(Dataset.project))
            .where(Dataset.user_id == user_id)
        )

        if project_id:
            query = query.where(Dataset.project_id == project_id)

        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Dataset.name.ilike(search_pattern),
                    Dataset.description.ilike(search_pattern),
                )
            )

        if status:
            query = query.where(Dataset.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(desc(Dataset.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total
