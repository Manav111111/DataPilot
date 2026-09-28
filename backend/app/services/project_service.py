from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException, ForbiddenException
from app.models.project import Project
from app.repositories.project_repo import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectDetailResponse, ProjectStatus


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.project_repo = ProjectRepository(db)

    async def create_project(self, user_id: str, data: ProjectCreate) -> ProjectResponse:
        project = Project(
            user_id=user_id,
            name=data.name.strip(),
            description=data.description.strip() if data.description else None,
            status=data.status.value if data.status else "draft",
        )
        project = await self.project_repo.create(project)
        return ProjectResponse(
            id=project.id,
            user_id=project.user_id,
            name=project.name,
            description=project.description,
            status=ProjectStatus(project.status),
            created_at=project.created_at,
            updated_at=project.updated_at,
            dataset_count=0,
            workflow_count=0,
        )

    async def get_project(self, project_id: str, user_id: str) -> ProjectDetailResponse:
        project = await self.project_repo.get_user_project(project_id, user_id)
        if not project:
            raise NotFoundException(detail="Project not found")

        d_count, w_count = await self.project_repo.get_project_counts(project_id)
        return ProjectDetailResponse(
            id=project.id,
            user_id=project.user_id,
            name=project.name,
            description=project.description,
            status=ProjectStatus(project.status),
            created_at=project.created_at,
            updated_at=project.updated_at,
            dataset_count=d_count,
            workflow_count=w_count,
        )

    async def list_projects(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Tuple[List[ProjectResponse], int]:
        projects, total = await self.project_repo.list_user_projects(
            user_id=user_id,
            skip=skip,
            limit=limit,
            search=search,
            status=status,
        )

        items = []
        for p in projects:
            d_count, w_count = await self.project_repo.get_project_counts(p.id)
            items.append(
                ProjectResponse(
                    id=p.id,
                    user_id=p.user_id,
                    name=p.name,
                    description=p.description,
                    status=ProjectStatus(p.status),
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                    dataset_count=d_count,
                    workflow_count=w_count,
                )
            )

        return items, total

    async def update_project(
        self, project_id: str, user_id: str, data: ProjectUpdate
    ) -> ProjectResponse:
        project = await self.project_repo.get_user_project(project_id, user_id)
        if not project:
            raise NotFoundException(detail="Project not found")

        if data.name is not None:
            project.name = data.name.strip()
        if data.description is not None:
            project.description = data.description.strip() if data.description else None
        if data.status is not None:
            project.status = data.status.value

        project = await self.project_repo.update(project)
        d_count, w_count = await self.project_repo.get_project_counts(project.id)

        return ProjectResponse(
            id=project.id,
            user_id=project.user_id,
            name=project.name,
            description=project.description,
            status=ProjectStatus(project.status),
            created_at=project.created_at,
            updated_at=project.updated_at,
            dataset_count=d_count,
            workflow_count=w_count,
        )

    async def delete_project(self, project_id: str, user_id: str) -> None:
        project = await self.project_repo.get_user_project(project_id, user_id)
        if not project:
            raise NotFoundException(detail="Project not found")

        await self.project_repo.delete(project)
