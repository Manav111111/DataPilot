SYSTEM_PLANNING_CORE = """You are an expert AI Data Architect and Intelligence Planning Agent.
Your job is to analyze natural-language data collection requests and generate structured, deterministic, reviewable data collection plans.
You MUST never claim data has been collected or accessed. This is strictly a planning and schema-definition stage.
Be precise, realistic about data availability, and identify potential challenges upfront."""

REQUEST_UNDERSTANDING_PROMPT = """Analyze the following user data requirement:

User Request: "{user_request}"
User-Provided Target Count: {target_count}
Clarification Answers (if any): {clarification_answers}

Tasks:
1. Identify the user's high-level goal.
2. Identify the target entity type (e.g., "Job Posting", "Company", "Real Estate Listing", "Academic Article", "Executive Profile").
3. Identify geographic constraints (e.g., "India", "Bengaluru", "United States", "Global").
4. Determine the target number of records to collect.
5. Extract requested required and optional fields.
6. Evaluate if the request is ambiguous, excessively vague, or lacking essential context (e.g., "get me info", "find data").
7. If ambiguous, generate 2-4 focused clarification questions to resolve the ambiguity.
"""

FIELD_SCHEMA_PROMPT = """Generate a comprehensive dataset field schema based on the understood data goal:

User Request: "{user_request}"
Goal: "{goal}"
Entity Type: "{entity_type}"
Target Fields Mentioned: Required={required_fields}, Optional={optional_fields}

Tasks:
1. For every field, define a snake_case name, a readable label, and a precise data type ('string', 'number', 'url', 'email', 'phone', 'date', 'boolean', 'array', 'object').
2. Explicitly determine if the field is mandatory (required=True) or optional (required=False).
3. State whether the value is commonly unavailable from public sources (allow_missing=True).
4. Clearly explain what data the field contains.
5. Include validation rules where applicable (e.g., 'valid_url', 'valid_email', 'min_length: 2').
6. Enforce a maximum of {max_fields} fields.
"""

SEARCH_STRATEGY_PROMPT = """Generate targeted web and directory search queries to find the requested data:

Goal: "{goal}"
Entity Type: "{entity_type}"
Geography: "{geography}"
Original Request: "{user_request}"

Tasks:
1. Create 3 to {max_queries} diverse, non-redundant search queries.
2. Specify the precise purpose of each query.
3. Categorize the source category targeted by each query (e.g. "Public Job Boards", "Company Career Portals", "Government Registries", "Public Company Directories").
4. Assign a priority integer from 1 (highest priority) to 5.
"""

SOURCE_RECOMMENDATION_PROMPT = """Recommend appropriate, permitted public data source categories:

Goal: "{goal}"
Entity Type: "{entity_type}"
Geography: "{geography}"

Tasks:
1. Recommend 2 to 5 relevant source categories.
2. Detail the exact rationale for why this source category is appropriate.
3. List the expected fields that can reliably be gathered from this category.
4. Detail potential limitations (e.g., rate limits, paywalls, anti-bot protections, stale data).
5. State any access requirements (e.g., "Public web access", "Requires public API credentials").
Do NOT claim that sources have been accessed or verified.
"""

QUALITY_RULES_PROMPT = """Define data validation, normalization, and deduplication rules:

Goal: "{goal}"
Entity Type: "{entity_type}"
Fields: {fields_summary}

Tasks:
1. Define a deduplication strategy tailored specifically to the entity type (e.g., normalized URL hash, combination of company name and job title).
2. Define format validation rules (e.g. valid URLs, valid emails).
3. Define geographic normalization rules if geography is specified.
4. Define record completeness and source attribution rules.
"""
