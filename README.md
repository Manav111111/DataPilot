# AI-Powered Data Intelligence Platform (Phase 1 & Phase 2)

A full-stack, enterprise-grade AI-Powered Data Intelligence Platform. The platform converts natural-language data collection requests into structured, reviewable, editable data collection plans using multi-step AI reasoning graphs (LangGraph), while maintaining projects, datasets, workflows, and strict multi-tenant isolation.

---

## 🚀 What's New in Phase 2: AI Planning Engine

Phase 2 introduces an intelligent planning layer that bridges user natural language prompts and structured data extraction blueprints:

1. **Multi-Step AI Planning Graph (LangGraph)**:
   - **Request Understanding Node**: Identifies entity type, geographic scope, target record count, and detects ambiguity.
   - **Field Schema Generation Node**: Infers clean typed field definitions (`string`, `number`, `url`, `date`, `boolean`, `email`, `phone`, `array`), required flags, and validation rules.
   - **Search Strategy Node**: Generates multi-angle keyword, dork, and filtered search queries categorized by intent (`broad`, `filtered`, `deep_dive`, `verification`) with priority levels (`high`, `medium`, `low`).
   - **Source Recommendation Node**: Suggests domain-specific data sources, rationale, expected fields, and collection limitations.
   - **Quality & Deduplication Rules Node**: Configures exact and fuzzy deduplication keys, null value tolerances, format regexes, and validation checks.
   - **Plan Assembly & Clarification Node**: Combines components into a single structured schema. If the prompt is ambiguous, marks status as `needs_clarification` and attaches targeted questions.

2. **Multi-LLM Provider Architecture**:
   - **Google Gemini** (`gemini-1.5-pro` / `gemini-1.5-flash`) via `google-generativeai` with structured JSON output modes.
   - **Groq** (`llama-3.3-70b-versatile` / `mixtral-8x7b-32768`) via `groq` SDK for ultra-fast planning latency.
   - **Deterministic Mock Provider**: Zero-config local fallback for offline development, CI/CD, and fast deterministic unit testing.
   - Dynamic key detection (`AIza...` for Gemini, `gsk_...` for Groq) with automatic fallback.

3. **Interactive Plan Review & Customization UI**:
   - **Natural Language Prompt Modal**: Includes pre-built prompt templates, target record count selectors, and step-by-step generation animations.
   - **Visual Field Builder**: Add, remove, reorder, and edit field names, types, descriptions, sample values, and required toggles.
   - **Search Query Editor**: Add custom search queries, modify search categories, and adjust query priorities.
   - **Interactive Clarification System**: Answer AI-generated clarifying questions to automatically re-tune the plan.
   - **Plan Regeneration with Feedback**: Submit natural language feedback to iteratively refine the blueprint before execution.
   - **Strict Approval Lifecycle**: Plans can be reviewed, edited, approved (`approved`), or rejected (`rejected`). Approval is safely blocked if clarifying questions remain unanswered.

---

## 🏗 Architecture & Tech Stack

### Frontend
- **Framework**: React 18 with Vite
- **Language**: TypeScript
- **Styling**: Tailwind CSS with custom SaaS light design system
- **Routing**: React Router v6 with public and protected routes
- **Server State**: TanStack Query (React Query) with optimistic cache invalidations
- **Form Handling**: React Hook Form with Zod schema validation
- **Icons**: Lucide React
- **HTTP Client**: Centralized Axios client with JWT interceptor & credentials

### Backend
- **Framework**: Python 3.11+ with FastAPI
- **AI / Agentic Graph**: LangGraph (`StateGraph`), LangChain Core
- **LLM Providers**: Google Gemini SDK (`google-generativeai`), Groq SDK (`groq`), Mock provider
- **Validation**: Pydantic v2 with strict schemas and `ConfigDict`
- **ORM & Database**: SQLAlchemy 2.0 (Async) + PostgreSQL (with SQLite async support for testing)
- **Migrations**: Alembic with auto-discovery and versioned schema history
- **Security & Auth**: Argon2 password hashing (`argon2-cffi`), JWT bearer token authentication, secure cookie handling
- **Testing**: Pytest + pytest-asyncio + HTTPX AsyncClient (25 automated integration tests)

---

## 📁 Monorepo Project Structure

```
data-intelligence-platform/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/          # MetricCard, StatusBadge, ConfirmDialog, SearchBar, Pagination
│   │   │   ├── layout/          # AppLayout, Navbar, Sidebar, ProtectedRoute, PublicRoute
│   │   │   └── ui/              # Button, Input, Textarea, Select, Card, Modal, Badge, Spinner, EmptyState, Toast
│   │   ├── features/
│   │   │   ├── auth/            # LoginForm, RegisterForm
│   │   │   ├── dashboard/       # RecentProjectsList, RecentDatasetsList, WorkflowRunsTable
│   │   │   ├── projects/        # ProjectCard, CreateProjectModal, EditProjectModal
│   │   │   ├── datasets/        # DatasetTable, CreateDatasetModal, EditDatasetModal, DatasetDetailsModal
│   │   │   └── plans/           # CreatePlanModal, PlanViewer, PlanCard, EditableFieldBuilder, SearchQueryEditor, SourceRecommendationPanel, QualityRulesPanel, ClarificationPanel
│   │   ├── hooks/               # useAuth, useProjects, useDatasets, useWorkflows, usePlans, useDashboard
│   │   ├── lib/                 # axios.ts, utils.ts
│   │   ├── services/            # authService, projectService, datasetService, workflowService, planService, dashboardService
│   │   ├── types/               # auth, project, dataset, workflow, plan, api
│   │   ├── pages/               # Login, Register, Dashboard, Projects, ProjectDetails, Datasets, Settings, NotFound
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   │   ├── graphs/          # planning_graph.py (LangGraph 6-node StateGraph)
│   │   │   └── providers/       # base.py, gemini.py, groq.py, mock.py, __init__.py (Factory)
│   │   ├── api/
│   │   │   ├── deps.py          # FastAPI auth & DB dependency injection
│   │   │   └── routes/          # auth, projects, datasets, plans, workflows, dashboard
│   │   ├── core/                # config, security (Argon2 + JWT), exceptions
│   │   ├── db/                  # session.py (AsyncSession), base.py
│   │   ├── models/              # User, Project, Dataset, CollectionPlan, WorkflowRun (SQLAlchemy 2.0)
│   │   ├── repositories/        # UserRepository, ProjectRepository, DatasetRepository, PlanRepository, WorkflowRepository
│   │   ├── schemas/             # Pydantic v2 schemas for all models, plans & DTOs
│   │   ├── services/            # AuthService, ProjectService, DatasetService, PlanService, WorkflowService
│   │   └── main.py              # FastAPI app lifecycle & router integration
│   ├── alembic/                 # Migration scripts (001_initial_schema, 002_collection_plans)
│   ├── tests/                   # Conftest & 25 comprehensive pytest async tests
│   ├── alembic.ini
│   ├── pytest.ini
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env` in the root:

```bash
cp .env.example .env
```

Key environment configuration:
| Variable | Description | Default |
|---|---|---|
| `ENVIRONMENT` | Runtime environment (`development`, `production`) | `development` |
| `DEBUG` | Debug mode | `True` |
| `SECRET_KEY` | Secret key for JWT encoding/decoding | `supersecretkey_change_in_production...` |
| `ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiration time | `1440` (24h) |
| `POSTGRES_SERVER` | PostgreSQL host | `localhost` (or `postgres` in Docker) |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `POSTGRES_USER` | PostgreSQL username | `postgres` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `postgres` |
| `POSTGRES_DB` | PostgreSQL database name | `data_intelligence_db` |
| `DATABASE_URL` | Full async connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/data_intelligence_db` |
| `AI_PROVIDER` | LLM provider (`gemini`, `groq`, `mock`) | `gemini` |
| `GEMINI_API_KEY` | Google Gemini API Key | `AIza...` |
| `GROQ_API_KEY` | Groq API Key | `gsk_...` |
| `MAX_PLAN_SEARCH_QUERIES`| Maximum search queries generated per plan | `10` |
| `MAX_PLAN_FIELDS` | Maximum field columns generated per plan | `25` |
| `VITE_API_BASE_URL` | Frontend API backend URL | `http://localhost:8000` |
| `BACKEND_CORS_ORIGINS` | Comma-separated allowed CORS origins | `http://localhost:5173,http://localhost:3000` |

---

## 📡 Collection Plan API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/projects/{project_id}/plans/generate` | Run AI planner to generate structured collection plan from natural language |
| `GET` | `/api/v1/projects/{project_id}/plans` | List all collection plans for a project |
| `GET` | `/api/v1/plans/{plan_id}` | Get full details and schema of a specific plan |
| `PATCH` | `/api/v1/plans/{plan_id}` | Update draft plan fields, search queries, target records, or metadata |
| `POST` | `/api/v1/plans/{plan_id}/approve` | Approve plan (validates that no clarification questions are pending) |
| `POST` | `/api/v1/plans/{plan_id}/reject` | Mark plan as rejected |
| `POST` | `/api/v1/plans/{plan_id}/regenerate` | Re-run AI planner with user feedback or clarification answers |

---

## 🚀 Quick Start with Docker Compose

To start the entire platform (PostgreSQL, FastAPI backend with auto-migrations, and React frontend) with a single command:

```bash
docker-compose up --build
```

- **Frontend Application**: [http://localhost:5173](http://localhost:5173)
- **Backend API Docs (Swagger)**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- **Backend ReDoc**: [http://localhost:8000/api/v1/redoc](http://localhost:8000/api/v1/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 💻 Local Development Setup (Without Docker)

### 1. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# On Windows:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run Alembic migrations (with Postgres running or configured)
alembic upgrade head

# Start FastAPI development server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

Visit [http://localhost:5173](http://localhost:5173).

---

## 🧪 Testing

### Backend Tests (Pytest)
Run the 25 comprehensive async integration, AI planner, and multi-tenant isolation tests:

```bash
cd backend
.\venv\Scripts\pytest.exe -v
```

**Test Coverage Highlights**:
- **AI Plan Generation**: Tests structured JSON extraction, field schema creation, and search query compilation.
- **Ambiguity & Clarifications**: Validates that vague inputs trigger `needs_clarification` status and clarification question generation.
- **Approval Validation Rule**: Enforces that plans cannot be approved while unresolved clarification questions remain.
- **Plan Modifications**: Tests editing field schemas, search queries, and metadata.
- **Feedback & Regeneration**: Tests re-prompting the AI graph with user feedback.
- **Strict Multi-Tenant Isolation**: Verified that User B cannot access, read, update, or approve User A's collection plans, projects, or datasets.
- **User Authentication & Auth Security**: Full Argon2 hashing, JWT verification, and protected route authorization.

### Frontend Build & Typecheck
```bash
cd frontend
npm run build
```

---

## 🔒 Security & Quality Features Implemented

1. **Password Hashing**: State-of-the-art Argon2id hashing with unique salting. Plaintext passwords are never stored or returned.
2. **JWT Security**: Strict HS256 JWT tokens with expiration claims and subject validation.
3. **Multi-Tenant Isolation**: Every database query is scoped by `user_id`. Attempting to access another user's project, dataset, or plan yields a strict `404 Not Found`.
4. **Foreign Key Integrity & Cascades**: Deleting a project automatically cascades to its plans, datasets, and workflow runs safely.
5. **Bounded AI Planning**: AI outputs are strictly structured and bounded by schema limits to prevent prompt injection and model hallucinations.
6. **Graceful Provider Fallback**: Automatic failover to mock provider if API keys are missing or unconfigured.

---

## 🧭 Phase 3 Readiness

This Phase 2 architecture is prepared for **Phase 3: Autonomous Web Collection & Extraction Engine**:
- Approved `CollectionPlan` objects contain structured `fields`, `search_queries`, `source_recommendations`, and `quality_rules`.
- In Phase 3, collection workers will read approved plans, execute search queries across web search APIs (Tavily, Firecrawl, Serper), extract content using LLM extractors against the plan's `FieldDefinition` schema, apply deduplication rules, and persist structured rows into `Dataset` records.

