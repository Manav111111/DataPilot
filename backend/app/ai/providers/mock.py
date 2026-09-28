import re
from typing import Type, TypeVar, Optional, List, Dict, Any
from pydantic import BaseModel
from app.ai.providers.base import BaseLLMProvider
from app.schemas.plan import (
    FieldDefinition,
    FieldType,
    SearchQuery,
    SourceRecommendation,
    QualityRule,
    RuleType,
    CollectionPlanData,
)

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(BaseLLMProvider):
    def get_provider_name(self) -> str:
        return "mock"

    def get_model_name(self) -> str:
        return "mock-intelligence-v1"

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
    ) -> T:
        prompt_lower = prompt.lower()

        # Extract user request if inside User Request: "..."
        req_match = re.search(r'user request:\s*"([^"]+)"', prompt, re.IGNORECASE)
        user_req = req_match.group(1).strip() if req_match else prompt.strip()
        user_req_lower = user_req.lower()

        # Check if the user request is ambiguous (e.g. "find data", "get info", "random stuff", or under 15 characters without concrete entities)
        has_specific_entity = any(
            w in user_req_lower
            for w in [
                "startup",
                "startups",
                "company",
                "companies",
                "job",
                "jobs",
                "hiring",
                "engineer",
                "engineers",
                "price",
                "prices",
                "real estate",
                "property",
                "leads",
                "products",
                "fintech",
            ]
        )
        is_ambiguous = (
            len(user_req) < 15 and not has_specific_entity
        ) or any(
            phrase in user_req_lower
            for phrase in ["find data", "get data", "give me info", "random stuff", "get things", "some data"]
        ) and not has_specific_entity

        schema_name = getattr(response_schema, "__name__", "")

        if schema_name == "RequestUnderstandingOutput":
            if is_ambiguous:
                return response_schema(
                    goal="Ambiguous data collection request requiring user clarification.",
                    entity_type="Unknown",
                    geography=None,
                    target_record_count=100,
                    required_fields=["id", "name"],
                    optional_fields=["description"],
                    is_ambiguous=True,
                    clarification_questions=[
                        "What specific entity or subject would you like to collect data on (e.g. companies, job postings, real estate listings)?",
                        "Are there any specific geographic constraints or industry categories?",
                        "What specific data attributes or columns are mandatory for your use case?",
                    ],
                )

            # Determine entity and geography from user_req
            geo = "India" if "india" in user_req_lower or "bengaluru" in user_req_lower or "bangalore" in user_req_lower or "mumbai" in user_req_lower else "Global"
            entity = "Job Posting" if "job" in user_req_lower or "hiring" in user_req_lower or "engineer" in user_req_lower else "Company"

            # Parse count if in prompt
            count_match = re.search(r"\b(\d+)\b", user_req)
            target_count = int(count_match.group(1)) if count_match else 100

            return response_schema(
                goal=f"Collect structured records of {entity.lower()}s based on criteria: {user_req}",
                entity_type=entity,
                geography=geo,
                target_record_count=target_count,
                required_fields=["company_name", "job_title", "job_url"] if entity == "Job Posting" else ["company_name", "website", "industry"],
                optional_fields=["salary", "location", "source"] if entity == "Job Posting" else ["funding", "headcount", "location"],
                is_ambiguous=False,
                clarification_questions=[],
            )

        if schema_name == "FieldSchemaOutput":
            if "job" in prompt_lower or "hiring" in prompt_lower or "engineer" in prompt_lower:
                fields = [
                    FieldDefinition(
                        name="company_name",
                        label="Company Name",
                        type=FieldType.STRING,
                        required=True,
                        description="Legal or commercial name of the hiring startup",
                        validation_rules=["min_length: 2"],
                        allow_missing=False,
                        requires_source_evidence=True,
                    ),
                    FieldDefinition(
                        name="job_title",
                        label="Job Title",
                        type=FieldType.STRING,
                        required=True,
                        description="Designation of the open position",
                        validation_rules=["min_length: 2"],
                        allow_missing=False,
                        requires_source_evidence=True,
                    ),
                    FieldDefinition(
                        name="location",
                        label="Location",
                        type=FieldType.STRING,
                        required=True,
                        description="City, state, or remote eligibility",
                        validation_rules=[],
                        allow_missing=False,
                        requires_source_evidence=True,
                    ),
                    FieldDefinition(
                        name="salary",
                        label="Salary / Compensation",
                        type=FieldType.STRING,
                        required=False,
                        description="Advertised compensation or salary range",
                        validation_rules=[],
                        allow_missing=True,
                        requires_source_evidence=False,
                    ),
                    FieldDefinition(
                        name="job_url",
                        label="Job Posting URL",
                        type=FieldType.URL,
                        required=True,
                        description="Canonical URL of the active job posting",
                        validation_rules=["valid_url"],
                        allow_missing=False,
                        requires_source_evidence=True,
                    ),
                    FieldDefinition(
                        name="company_website",
                        label="Company Website",
                        type=FieldType.URL,
                        required=False,
                        description="Official homepage URL of the company",
                        validation_rules=["valid_url"],
                        allow_missing=True,
                        requires_source_evidence=False,
                    ),
                    FieldDefinition(
                        name="source",
                        label="Source Platform",
                        type=FieldType.STRING,
                        required=True,
                        description="Origin domain or job board where listing was discovered",
                        validation_rules=[],
                        allow_missing=False,
                        requires_source_evidence=True,
                    ),
                ]
            else:
                fields = [
                    FieldDefinition(
                        name="company_name",
                        label="Company Name",
                        type=FieldType.STRING,
                        required=True,
                        description="Official company name",
                        validation_rules=["min_length: 2"],
                        allow_missing=False,
                        requires_source_evidence=True,
                    ),
                    FieldDefinition(
                        name="website",
                        label="Website URL",
                        type=FieldType.URL,
                        required=True,
                        description="Company website URL",
                        validation_rules=["valid_url"],
                        allow_missing=False,
                        requires_source_evidence=True,
                    ),
                    FieldDefinition(
                        name="industry",
                        label="Industry / Domain",
                        type=FieldType.STRING,
                        required=True,
                        description="Primary industry category",
                        validation_rules=[],
                        allow_missing=False,
                        requires_source_evidence=True,
                    ),
                    FieldDefinition(
                        name="location",
                        label="Headquarters Location",
                        type=FieldType.STRING,
                        required=False,
                        description="City and country of headquarters",
                        validation_rules=[],
                        allow_missing=True,
                        requires_source_evidence=False,
                    ),
                ]
            return response_schema(fields=fields)

        if schema_name == "SearchStrategyOutput":
            queries = [
                SearchQuery(
                    query="Indian startups hiring AI ML engineers career portal",
                    purpose="Discover direct career page listings from Indian technology startups",
                    source_category="Company Career Pages",
                    geography="India",
                    priority=1,
                ),
                SearchQuery(
                    query="Machine learning engineer openings Bangalore startups public job board",
                    purpose="Identify active job postings from tech hubs across India",
                    source_category="Public Job Boards",
                    geography="Bengaluru, India",
                    priority=2,
                ),
                SearchQuery(
                    query="site:linkedin.com/jobs AI engineer startup India",
                    purpose="Locate public job announcements from early and growth stage startups",
                    source_category="Public Directories & Boards",
                    geography="India",
                    priority=3,
                ),
            ]
            return response_schema(queries=queries)

        if schema_name == "SourceRecommendationOutput":
            sources = [
                SourceRecommendation(
                    source_category="Official Company Career Portals",
                    rationale="Direct source of truth for hiring vacancies and compensation specifications",
                    expected_fields=["company_name", "job_title", "location", "salary", "job_url"],
                    limitations="Each company has custom layouts and varying update frequencies",
                    access_requirements="Public web access",
                ),
                SourceRecommendation(
                    source_category="Public Job Aggregators & Boards",
                    rationale="High volume of aggregated startup job postings with structured attributes",
                    expected_fields=["job_title", "company_name", "location", "source"],
                    limitations="Listings may occasionally be duplicate or expired",
                    access_requirements="Public directory access",
                ),
                SourceRecommendation(
                    source_category="Public Startup Ecosystem Directories",
                    rationale="Useful for verifying company domain, founding year, and active operation",
                    expected_fields=["company_name", "company_website", "industry"],
                    limitations="May not contain real-time daily hiring status",
                    access_requirements="Public dataset access",
                ),
            ]
            return response_schema(sources=sources)

        if schema_name == "QualityRulesOutput":
            rules = [
                QualityRule(
                    name="Job URL Format Validation",
                    description="Ensure all collected job_url values are well-formed absolute URLs with http/https schemes",
                    rule_type=RuleType.VALID_URL,
                    field="job_url",
                    configuration={"protocol": ["http", "https"], "require_tld": True},
                ),
                QualityRule(
                    name="Deduplication by URL and Title",
                    description="Deduplicate records having identical normalized job URLs or matching company and job title combinations",
                    rule_type=RuleType.DUPLICATE_CHECK,
                    field="job_url",
                    configuration={"strategy": "url_and_title_hash", "case_insensitive": True},
                ),
                QualityRule(
                    name="Geographic Normalization",
                    description="Standardize Indian city names (e.g. Bangalore -> Bengaluru, Bombay -> Mumbai)",
                    rule_type=RuleType.GEO_NORMALIZATION,
                    field="location",
                    configuration={"target_country": "India"},
                ),
                QualityRule(
                    name="Mandatory Attribution",
                    description="Ensure every extracted record includes verified source URL evidence",
                    rule_type=RuleType.SOURCE_ATTRIBUTION,
                    field="source",
                    configuration={"require_timestamp": True},
                ),
            ]
            return response_schema(rules=rules)

        # Default fallback
        data = {
            "goal": "Collect structured intelligence records based on requirements.",
            "entity_type": "Record",
            "geography": "Global",
            "target_record_count": 100,
            "fields": [],
            "search_queries": [],
            "source_recommendations": [],
            "filters": [],
            "quality_rules": [],
            "execution_steps": [
                "Step 1: Execute proposed search queries against permitted public sources",
                "Step 2: Parse raw page metadata and identify target entity candidates",
                "Step 3: Extract structured field values in accordance with schema rules",
                "Step 4: Run deduplication and validation pipelines",
                "Step 5: Output verified records into project dataset table",
            ],
            "assumptions": ["Sources provide accessible public HTML without authentication walls."],
            "limitations": ["Salary disclosures are optional on most job postings and may be unavailable."],
            "clarification_questions": [],
        }
        return response_schema.model_validate(data)
