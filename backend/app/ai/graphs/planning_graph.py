import logging
from typing import TypedDict, List, Optional, Dict, Any
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from app.ai.providers.base import BaseLLMProvider
from app.ai.providers import get_llm_provider
from app.ai.prompts.planning_prompts import (
    SYSTEM_PLANNING_CORE,
    REQUEST_UNDERSTANDING_PROMPT,
    FIELD_SCHEMA_PROMPT,
    SEARCH_STRATEGY_PROMPT,
    SOURCE_RECOMMENDATION_PROMPT,
    QUALITY_RULES_PROMPT,
)
from app.schemas.plan import (
    PlanStatus,
    FieldDefinition,
    FieldType,
    SearchQuery,
    SourceRecommendation,
    QualityRule,
    RuleType,
    CollectionPlanData,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


# Pydantic models for structured node outputs
class RequestUnderstandingOutput(BaseModel):
    goal: str
    entity_type: str
    geography: Optional[str] = None
    target_record_count: int = 100
    required_fields: List[str] = Field(default_factory=list)
    optional_fields: List[str] = Field(default_factory=list)
    is_ambiguous: bool = False
    clarification_questions: List[str] = Field(default_factory=list)


class FieldSchemaOutput(BaseModel):
    fields: List[FieldDefinition]


class SearchStrategyOutput(BaseModel):
    queries: List[SearchQuery]


class SourceRecommendationOutput(BaseModel):
    sources: List[SourceRecommendation]


class QualityRulesOutput(BaseModel):
    rules: List[QualityRule]


# Planning State
class PlanningState(TypedDict):
    user_request: str
    target_record_count: int
    clarification_answers: Optional[Dict[str, str]]
    feedback: Optional[str]
    goal: Optional[str]
    entity_type: Optional[str]
    geography: Optional[str]
    required_fields: Optional[List[str]]
    optional_fields: Optional[List[str]]
    is_ambiguous: bool
    clarification_questions: List[str]
    fields: List[FieldDefinition]
    search_queries: List[SearchQuery]
    source_recommendations: List[SourceRecommendation]
    quality_rules: List[QualityRule]
    execution_steps: List[str]
    assumptions: List[str]
    limitations: List[str]
    final_plan: Optional[CollectionPlanData]
    status: PlanStatus
    provider_name: str
    model_name: str


class PlanningGraphRunner:
    def __init__(self, provider: Optional[BaseLLMProvider] = None):
        self.provider = provider or get_llm_provider()
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(PlanningState)

        builder.add_node("understand_request", self._node_understand_request)
        builder.add_node("generate_schema", self._node_generate_schema)
        builder.add_node("generate_search", self._node_generate_search)
        builder.add_node("recommend_sources", self._node_recommend_sources)
        builder.add_node("generate_quality_rules", self._node_generate_quality_rules)
        builder.add_node("assemble_plan", self._node_assemble_plan)

        builder.set_entry_point("understand_request")

        # Conditional edge based on ambiguity
        def check_ambiguity(state: PlanningState) -> str:
            if state.get("is_ambiguous") and state.get("clarification_questions"):
                return "assemble_plan"
            return "generate_schema"

        builder.add_conditional_edges(
            "understand_request",
            check_ambiguity,
            {
                "assemble_plan": "assemble_plan",
                "generate_schema": "generate_schema",
            },
        )

        builder.add_edge("generate_schema", "generate_search")
        builder.add_edge("generate_search", "recommend_sources")
        builder.add_edge("recommend_sources", "generate_quality_rules")
        builder.add_edge("generate_quality_rules", "assemble_plan")
        builder.add_edge("assemble_plan", END)

        return builder.compile()

    async def _node_understand_request(self, state: PlanningState) -> Dict[str, Any]:
        prompt = REQUEST_UNDERSTANDING_PROMPT.format(
            user_request=state["user_request"],
            target_count=state.get("target_record_count", 100),
            clarification_answers=state.get("clarification_answers") or "None",
        )

        if state.get("feedback"):
            prompt += f"\nUser Feedback from previous iteration: {state['feedback']}"

        try:
            res: RequestUnderstandingOutput = await self.provider.generate_structured(
                prompt=prompt,
                response_schema=RequestUnderstandingOutput,
                system_instruction=SYSTEM_PLANNING_CORE,
            )

            # Cap record count
            target_count = min(
                state.get("target_record_count") or res.target_record_count,
                settings.AI_PLANNING_MAX_RECORDS,
            )

            return {
                "goal": res.goal,
                "entity_type": res.entity_type,
                "geography": res.geography,
                "target_record_count": target_count,
                "required_fields": res.required_fields,
                "optional_fields": res.optional_fields,
                "is_ambiguous": res.is_ambiguous,
                "clarification_questions": res.clarification_questions,
            }
        except Exception as e:
            logger.error(f"Error in understand_request node: {e}")
            return {
                "goal": f"Collect structured data according to request: {state['user_request']}",
                "entity_type": "Data Record",
                "geography": "Global",
                "target_record_count": state.get("target_record_count", 100),
                "required_fields": ["name", "url"],
                "optional_fields": ["description", "category"],
                "is_ambiguous": False,
                "clarification_questions": [],
            }

    async def _node_generate_schema(self, state: PlanningState) -> Dict[str, Any]:
        prompt = FIELD_SCHEMA_PROMPT.format(
            user_request=state["user_request"],
            goal=state.get("goal", ""),
            entity_type=state.get("entity_type", "Record"),
            required_fields=", ".join(state.get("required_fields", [])),
            optional_fields=", ".join(state.get("optional_fields", [])),
            max_fields=settings.AI_PLANNING_MAX_FIELDS,
        )

        try:
            res: FieldSchemaOutput = await self.provider.generate_structured(
                prompt=prompt,
                response_schema=FieldSchemaOutput,
                system_instruction=SYSTEM_PLANNING_CORE,
            )
            # Enforce max field limits and ensure unique snake_case names
            fields = []
            seen = set()
            for f in res.fields[: settings.AI_PLANNING_MAX_FIELDS]:
                clean_name = f.name.lower().replace(" ", "_")
                if clean_name not in seen:
                    seen.add(clean_name)
                    f.name = clean_name
                    fields.append(f)
            return {"fields": fields}
        except Exception as e:
            logger.error(f"Error in generate_schema node: {e}")
            return {
                "fields": [
                    FieldDefinition(
                        name="title",
                        label="Title / Name",
                        type=FieldType.STRING,
                        required=True,
                        description="Primary name or title",
                    ),
                    FieldDefinition(
                        name="source_url",
                        label="Source URL",
                        type=FieldType.URL,
                        required=True,
                        description="Origin web link",
                        validation_rules=["valid_url"],
                    ),
                ]
            }

    async def _node_generate_search(self, state: PlanningState) -> Dict[str, Any]:
        prompt = SEARCH_STRATEGY_PROMPT.format(
            goal=state.get("goal", ""),
            entity_type=state.get("entity_type", "Record"),
            geography=state.get("geography", "Global"),
            user_request=state["user_request"],
            max_queries=settings.AI_PLANNING_MAX_QUERIES,
        )

        try:
            res: SearchStrategyOutput = await self.provider.generate_structured(
                prompt=prompt,
                response_schema=SearchStrategyOutput,
                system_instruction=SYSTEM_PLANNING_CORE,
            )
            return {"search_queries": res.queries[: settings.AI_PLANNING_MAX_QUERIES]}
        except Exception as e:
            logger.error(f"Error in generate_search node: {e}")
            return {
                "search_queries": [
                    SearchQuery(
                        query=f"{state.get('entity_type', 'Data')} {state.get('geography', '')} public listings",
                        purpose="Locate primary candidate pages",
                        source_category="Public Web",
                        geography=state.get("geography"),
                        priority=1,
                    )
                ]
            }

    async def _node_recommend_sources(self, state: PlanningState) -> Dict[str, Any]:
        prompt = SOURCE_RECOMMENDATION_PROMPT.format(
            goal=state.get("goal", ""),
            entity_type=state.get("entity_type", "Record"),
            geography=state.get("geography", "Global"),
        )

        try:
            res: SourceRecommendationOutput = await self.provider.generate_structured(
                prompt=prompt,
                response_schema=SourceRecommendationOutput,
                system_instruction=SYSTEM_PLANNING_CORE,
            )
            return {"source_recommendations": res.sources}
        except Exception as e:
            logger.error(f"Error in recommend_sources node: {e}")
            return {
                "source_recommendations": [
                    SourceRecommendation(
                        source_category="Public Directories & Web Portals",
                        rationale="Broadest coverage of publicly indexable listings",
                        expected_fields=["title", "source_url"],
                        limitations="Varying page formats and rate limits",
                        access_requirements="Public access",
                    )
                ]
            }

    async def _node_generate_quality_rules(self, state: PlanningState) -> Dict[str, Any]:
        fields_summary = ", ".join([f.name for f in state.get("fields", [])])
        prompt = QUALITY_RULES_PROMPT.format(
            goal=state.get("goal", ""),
            entity_type=state.get("entity_type", "Record"),
            fields_summary=fields_summary,
        )

        try:
            res: QualityRulesOutput = await self.provider.generate_structured(
                prompt=prompt,
                response_schema=QualityRulesOutput,
                system_instruction=SYSTEM_PLANNING_CORE,
            )
            return {"quality_rules": res.rules}
        except Exception as e:
            logger.error(f"Error in generate_quality_rules node: {e}")
            return {
                "quality_rules": [
                    QualityRule(
                        name="URL Validation",
                        description="Ensure all URL fields contain valid web addresses",
                        rule_type=RuleType.VALID_URL,
                    ),
                    QualityRule(
                        name="Duplicate Check",
                        description="Deduplicate records with matching URLs or primary titles",
                        rule_type=RuleType.DUPLICATE_CHECK,
                    ),
                ]
            }

    async def _node_assemble_plan(self, state: PlanningState) -> Dict[str, Any]:
        is_ambiguous = state.get("is_ambiguous", False)
        clarification_questions = state.get("clarification_questions", [])

        status = (
            PlanStatus.NEEDS_CLARIFICATION
            if (is_ambiguous and clarification_questions)
            else PlanStatus.READY_FOR_REVIEW
        )

        execution_steps = [
            "Step 1: Execute query plan across recommended public sources (Phase 3)",
            "Step 2: Parse raw HTML/JSON structures and extract candidate entity elements",
            "Step 3: Validate extracted values against defined schema rules and types",
            "Step 4: Execute deduplication pipelines across canonical identifiers",
            "Step 5: Output structured records into project dataset table",
        ]

        assumptions = [
            "Target data sources remain publicly accessible without requiring paid authentication.",
            "Relevant records are discoverable via standard search indexing queries.",
        ]

        limitations = [
            "Certain fields (e.g. private contact numbers or unadvertised salaries) may be sparse or omitted by employers.",
            "Data extraction velocity is bounded by respectful rate limits and source availability.",
        ]

        plan_data = CollectionPlanData(
            goal=state.get("goal") or state["user_request"],
            entity_type=state.get("entity_type") or "Record",
            geography=state.get("geography"),
            target_record_count=state.get("target_record_count", 100),
            fields=state.get("fields", []),
            search_queries=state.get("search_queries", []),
            source_recommendations=state.get("source_recommendations", []),
            filters=state.get("filters", []),
            quality_rules=state.get("quality_rules", []),
            execution_steps=execution_steps,
            assumptions=assumptions,
            limitations=limitations,
            clarification_questions=clarification_questions,
        )

        return {
            "final_plan": plan_data,
            "status": status,
            "provider_name": self.provider.get_provider_name(),
            "model_name": self.provider.get_model_name(),
        }

    async def execute(
        self,
        user_request: str,
        target_record_count: Optional[int] = 100,
        clarification_answers: Optional[Dict[str, str]] = None,
        feedback: Optional[str] = None,
    ) -> PlanningState:
        initial_state: PlanningState = {
            "user_request": user_request,
            "target_record_count": target_record_count or 100,
            "clarification_answers": clarification_answers,
            "feedback": feedback,
            "goal": None,
            "entity_type": None,
            "geography": None,
            "required_fields": [],
            "optional_fields": [],
            "is_ambiguous": False,
            "clarification_questions": [],
            "fields": [],
            "search_queries": [],
            "source_recommendations": [],
            "quality_rules": [],
            "execution_steps": [],
            "assumptions": [],
            "limitations": [],
            "final_plan": None,
            "status": PlanStatus.DRAFT,
            "provider_name": self.provider.get_provider_name(),
            "model_name": self.provider.get_model_name(),
        }

        result = await self.graph.ainvoke(initial_state)
        return result
