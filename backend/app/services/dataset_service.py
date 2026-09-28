from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException, ForbiddenException
from app.models.dataset import Dataset
from app.repositories.dataset_repo import DatasetRepository
from app.repositories.project_repo import ProjectRepository
from app.schemas.dataset import DatasetCreate, DatasetUpdate, DatasetResponse, DatasetStatus


class DatasetService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.dataset_repo = DatasetRepository(db)
        self.project_repo = ProjectRepository(db)

    async def create_dataset(self, user_id: str, data: DatasetCreate) -> DatasetResponse:
        # Check project ownership
        project = await self.project_repo.get_user_project(data.project_id, user_id)
        if not project:
            raise NotFoundException(detail="Project not found or does not belong to you")

        dataset = Dataset(
            project_id=data.project_id,
            user_id=user_id,
            name=data.name.strip(),
            description=data.description.strip() if data.description else None,
            status=data.status.value if data.status else "pending",
            row_count=data.row_count or 0,
        )
        dataset = await self.dataset_repo.create(dataset)
        return DatasetResponse(
            id=dataset.id,
            project_id=dataset.project_id,
            user_id=dataset.user_id,
            name=dataset.name,
            description=dataset.description,
            status=DatasetStatus(dataset.status),
            row_count=dataset.row_count,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
            project_name=project.name,
        )

    async def get_dataset(self, dataset_id: str, user_id: str) -> DatasetResponse:
        dataset = await self.dataset_repo.get_user_dataset(dataset_id, user_id)
        if not dataset:
            raise NotFoundException(detail="Dataset not found")

        return DatasetResponse(
            id=dataset.id,
            project_id=dataset.project_id,
            user_id=dataset.user_id,
            name=dataset.name,
            description=dataset.description,
            status=DatasetStatus(dataset.status),
            row_count=dataset.row_count,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
            project_name=dataset.project.name if dataset.project else None,
        )

    async def list_datasets(
        self,
        user_id: str,
        project_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Tuple[List[DatasetResponse], int]:
        datasets, total = await self.dataset_repo.list_user_datasets(
            user_id=user_id,
            project_id=project_id,
            skip=skip,
            limit=limit,
            search=search,
            status=status,
        )

        items = [
            DatasetResponse(
                id=d.id,
                project_id=d.project_id,
                user_id=d.user_id,
                name=d.name,
                description=d.description,
                status=DatasetStatus(d.status),
                row_count=d.row_count,
                created_at=d.created_at,
                updated_at=d.updated_at,
                project_name=d.project.name if d.project else None,
            )
            for d in datasets
        ]

        return items, total

    async def update_dataset(
        self, dataset_id: str, user_id: str, data: DatasetUpdate
    ) -> DatasetResponse:
        dataset = await self.dataset_repo.get_user_dataset(dataset_id, user_id)
        if not dataset:
            raise NotFoundException(detail="Dataset not found")

        if data.name is not None:
            dataset.name = data.name.strip()
        if data.description is not None:
            dataset.description = data.description.strip() if data.description else None
        if data.status is not None:
            dataset.status = data.status.value
        if data.row_count is not None:
            dataset.row_count = data.row_count

        dataset = await self.dataset_repo.update(dataset)
        return DatasetResponse(
            id=dataset.id,
            project_id=dataset.project_id,
            user_id=dataset.user_id,
            name=dataset.name,
            description=dataset.description,
            status=DatasetStatus(dataset.status),
            row_count=dataset.row_count,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
            project_name=dataset.project.name if dataset.project else None,
        )

    async def delete_dataset(self, dataset_id: str, user_id: str) -> None:
        dataset = await self.dataset_repo.get_user_dataset(dataset_id, user_id)
        if not dataset:
            raise NotFoundException(detail="Dataset not found")

        await self.dataset_repo.delete(dataset)
