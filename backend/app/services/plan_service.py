from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException, BadRequestException, ForbiddenException
from app.models.plan import CollectionPlan
from app.repositories.plan_repo import PlanRepository
from app.repositories.project_repo import ProjectRepository
from app.schemas.plan import (
    PlanStatus,
    GeneratePlanRequest,
    UpdatePlanRequest,
    RegeneratePlanRequest,
    CollectionPlanResponse,
    CollectionPlanData,
    FieldDefinition,
)
from app.ai.graphs.planning_graph import PlanningGraphRunner
from app.ai.providers import get_llm_provider


class PlanService:
    def __init__(self, db: AsyncSession, graph_runner: Optional[PlanningGraphRunner] = None):
        self.db = db
        self.plan_repo = PlanRepository(db)
        self.project_repo = ProjectRepository(db)
        self.graph_runner = graph_runner or PlanningGraphRunner()

    async def generate_plan(
        self, user_id: str, project_id: str, req: GeneratePlanRequest
    ) -> CollectionPlanResponse:
        # Check project ownership
        project = await self.project_repo.get_user_project(project_id, user_id)
        if not project:
            raise NotFoundException(detail="Project not found or does not belong to you")

        # Execute AI planning graph
        graph_result = await self.graph_runner.execute(
            user_request=req.request.strip(),
            target_record_count=req.target_record_count or 100,
            clarification_answers=req.clarification_answers,
        )

        final_plan: CollectionPlanData = graph_result["final_plan"]
        status: PlanStatus = graph_result["status"]

        # Persist CollectionPlan
        plan = CollectionPlan(
            user_id=user_id,
            project_id=project_id,
            original_request=req.request.strip(),
            status=status.value,
            plan_data=final_plan.model_dump(),
            provider_metadata={
                "provider": graph_result.get("provider_name"),
                "model": graph_result.get("model_name"),
            },
        )
        plan = await self.plan_repo.create(plan)

        return CollectionPlanResponse(
            id=plan.id,
            user_id=plan.user_id,
            project_id=plan.project_id,
            original_request=plan.original_request,
            status=PlanStatus(plan.status),
            plan_data=CollectionPlanData.model_validate(plan.plan_data),
            provider_metadata=plan.provider_metadata,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
            project_name=project.name,
        )

    async def get_plan(self, plan_id: str, user_id: str) -> CollectionPlanResponse:
        plan = await self.plan_repo.get_user_plan(plan_id, user_id)
        if not plan:
            raise NotFoundException(detail="Collection plan not found")

        return CollectionPlanResponse(
            id=plan.id,
            user_id=plan.user_id,
            project_id=plan.project_id,
            original_request=plan.original_request,
            status=PlanStatus(plan.status),
            plan_data=CollectionPlanData.model_validate(plan.plan_data),
            provider_metadata=plan.provider_metadata,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
            project_name=plan.project.name if plan.project else None,
        )

    async def list_project_plans(
        self,
        project_id: str,
        user_id: str,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[CollectionPlanResponse], int]:
        project = await self.project_repo.get_user_project(project_id, user_id)
        if not project:
            raise NotFoundException(detail="Project not found or does not belong to you")

        plans, total = await self.plan_repo.list_project_plans(
            project_id=project_id,
            user_id=user_id,
            status=status,
            skip=skip,
            limit=limit,
        )

        items = [
            CollectionPlanResponse(
                id=p.id,
                user_id=p.user_id,
                project_id=p.project_id,
                original_request=p.original_request,
                status=PlanStatus(p.status),
                plan_data=CollectionPlanData.model_validate(p.plan_data),
                provider_metadata=p.provider_metadata,
                created_at=p.created_at,
                updated_at=p.updated_at,
                project_name=p.project.name if p.project else None,
            )
            for p in plans
        ]

        return items, total

    async def update_plan(
        self, plan_id: str, user_id: str, req: UpdatePlanRequest
    ) -> CollectionPlanResponse:
        plan = await self.plan_repo.get_user_plan(plan_id, user_id)
        if not plan:
            raise NotFoundException(detail="Collection plan not found")

        current_data = CollectionPlanData.model_validate(plan.plan_data)

        if req.goal is not None:
            current_data.goal = req.goal.strip()
        if req.entity_type is not None:
            current_data.entity_type = req.entity_type.strip()
        if req.geography is not None:
            current_data.geography = req.geography.strip()
        if req.target_record_count is not None:
            current_data.target_record_count = req.target_record_count
        if req.fields is not None:
            # Validate field uniqueness
            seen_names = set()
            for f in req.fields:
                name_clean = f.name.strip().lower()
                if name_clean in seen_names:
                    raise BadRequestException(detail=f"Duplicate field name '{f.name}' in schema")
                seen_names.add(name_clean)
            current_data.fields = req.fields
        if req.search_queries is not None:
            current_data.search_queries = req.search_queries
        if req.source_recommendations is not None:
            current_data.source_recommendations = req.source_recommendations
        if req.filters is not None:
            current_data.filters = req.filters
        if req.quality_rules is not None:
            current_data.quality_rules = req.quality_rules
        if req.assumptions is not None:
            current_data.assumptions = req.assumptions
        if req.limitations is not None:
            current_data.limitations = req.limitations

        # If it was in needs_clarification and fields/goal are set, can switch to draft/ready_for_review
        if plan.status == PlanStatus.NEEDS_CLARIFICATION.value and len(current_data.fields) > 0:
            plan.status = PlanStatus.READY_FOR_REVIEW.value

        plan.plan_data = current_data.model_dump()
        plan = await self.plan_repo.update(plan)

        return CollectionPlanResponse(
            id=plan.id,
            user_id=plan.user_id,
            project_id=plan.project_id,
            original_request=plan.original_request,
            status=PlanStatus(plan.status),
            plan_data=CollectionPlanData.model_validate(plan.plan_data),
            provider_metadata=plan.provider_metadata,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
            project_name=plan.project.name if plan.project else None,
        )

    async def approve_plan(self, plan_id: str, user_id: str) -> CollectionPlanResponse:
        plan = await self.plan_repo.get_user_plan(plan_id, user_id)
        if not plan:
            raise NotFoundException(detail="Collection plan not found")

        plan_data = CollectionPlanData.model_validate(plan.plan_data)

        # Check that plan is valid for approval
        if plan.status == PlanStatus.NEEDS_CLARIFICATION.value and plan_data.clarification_questions:
            raise BadRequestException(
                detail="Cannot approve plan with unresolved essential clarification questions. Please answer questions and regenerate first."
            )

        if not plan_data.fields:
            raise BadRequestException(detail="Cannot approve plan without at least one field definition.")

        plan.status = PlanStatus.APPROVED.value
        plan = await self.plan_repo.update(plan)

        return CollectionPlanResponse(
            id=plan.id,
            user_id=plan.user_id,
            project_id=plan.project_id,
            original_request=plan.original_request,
            status=PlanStatus(plan.status),
            plan_data=plan_data,
            provider_metadata=plan.provider_metadata,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
            project_name=plan.project.name if plan.project else None,
        )

    async def reject_plan(self, plan_id: str, user_id: str) -> CollectionPlanResponse:
        plan = await self.plan_repo.get_user_plan(plan_id, user_id)
        if not plan:
            raise NotFoundException(detail="Collection plan not found")

        plan.status = PlanStatus.REJECTED.value
        plan = await self.plan_repo.update(plan)

        return CollectionPlanResponse(
            id=plan.id,
            user_id=plan.user_id,
            project_id=plan.project_id,
            original_request=plan.original_request,
            status=PlanStatus(plan.status),
            plan_data=CollectionPlanData.model_validate(plan.plan_data),
            provider_metadata=plan.provider_metadata,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
            project_name=plan.project.name if plan.project else None,
        )

    async def regenerate_plan(
        self, plan_id: str, user_id: str, req: RegeneratePlanRequest
    ) -> CollectionPlanResponse:
        plan = await self.plan_repo.get_user_plan(plan_id, user_id)
        if not plan:
            raise NotFoundException(detail="Collection plan not found")

        current_data = CollectionPlanData.model_validate(plan.plan_data)

        # Execute AI planning graph with original request + feedback + clarification answers
        graph_result = await self.graph_runner.execute(
            user_request=plan.original_request,
            target_record_count=current_data.target_record_count,
            clarification_answers=req.clarification_answers,
            feedback=req.feedback,
        )

        final_plan: CollectionPlanData = graph_result["final_plan"]
        status: PlanStatus = graph_result["status"]

        plan.plan_data = final_plan.model_dump()
        plan.status = status.value
        plan.provider_metadata = {
            "provider": graph_result.get("provider_name"),
            "model": graph_result.get("model_name"),
        }

        plan = await self.plan_repo.update(plan)

        return CollectionPlanResponse(
            id=plan.id,
            user_id=plan.user_id,
            project_id=plan.project_id,
            original_request=plan.original_request,
            status=PlanStatus(plan.status),
            plan_data=CollectionPlanData.model_validate(plan.plan_data),
            provider_metadata=plan.provider_metadata,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
            project_name=plan.project.name if plan.project else None,
        )
