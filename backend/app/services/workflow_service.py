from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException
from app.models.workflow import WorkflowRun
from app.repositories.workflow_repo import WorkflowRepository
from app.repositories.project_repo import ProjectRepository
from app.schemas.workflow import WorkflowRunCreate, WorkflowRunResponse, WorkflowStatus


class WorkflowService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.workflow_repo = WorkflowRepository(db)
        self.project_repo = ProjectRepository(db)

    async def list_workflows(
        self,
        user_id: str,
        project_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[WorkflowRunResponse], int]:
        workflows, total = await self.workflow_repo.list_user_workflows(
            user_id=user_id,
            project_id=project_id,
            skip=skip,
            limit=limit,
        )

        items = [
            WorkflowRunResponse(
                id=w.id,
                project_id=w.project_id,
                user_id=w.user_id,
                status=WorkflowStatus(w.status),
                started_at=w.started_at,
                completed_at=w.completed_at,
                error_message=w.error_message,
                created_at=w.created_at,
                project_name=w.project.name if w.project else None,
            )
            for w in workflows
        ]

        return items, total

    async def get_workflow(
        self, workflow_id: str, user_id: str
    ) -> WorkflowRunResponse:
        workflow = await self.workflow_repo.get_user_workflow(workflow_id, user_id)
        if not workflow:
            raise NotFoundException(detail="Workflow run not found")

        return WorkflowRunResponse(
            id=workflow.id,
            project_id=workflow.project_id,
            user_id=workflow.user_id,
            status=WorkflowStatus(workflow.status),
            started_at=workflow.started_at,
            completed_at=workflow.completed_at,
            error_message=workflow.error_message,
            created_at=workflow.created_at,
            project_name=workflow.project.name if workflow.project else None,
        )
