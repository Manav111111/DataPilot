# DataPilot — AI-Powered Data Intelligence Platform (Phases 1, 2, 3, 4 & 5)

A full-stack, enterprise-grade AI-Powered Data Intelligence Platform. The platform converts natural-language data collection requests into structured, reviewable, editable data collection plans using multi-step AI reasoning graphs (LangGraph), executes autonomous web data collection with source-backed provenance using Tavily, Firecrawl, Celery, Redis, and LLM structured extraction, provides comprehensive **Data Quality Profiling, Interactive Cleaning, Safe Transformations, Visual Analytics, Duplicate Merging, CSV/Excel/JSON Exports, Dataset Versioning**, and delivers **AI-Powered Natural-Language Dataset Chat, Deterministic Pandas Analytical Engine, Automated Multi-Dimensional Auto-Insights, Statistical Profiling, Dynamic Inline Visualizations, and Standalone Executive Report Builder**.

---

## 🚀 What's New in Phase 5: AI Insights & Intelligent Data Analysis

Phase 5 transforms DataPilot into a full-scale AI data analysis workspace where users can query, analyze, and generate comprehensive intelligence reports from their collected datasets using natural language:

1. **AI-Powered Dataset Chat & Natural Language Querying**:
   - Conversational analyst assistant integrated directly into dataset workspaces.
   - Converts natural-language user inquiries into structured analytical plans without ever inventing data, metrics, or conclusions.
   - Real-time execution against actual stored PostgreSQL dataset records using Pandas.
   - Dynamic inline rendering of verified result tables, analytical explanations, and responsive charts.
   - Smart suggested prompt chips tailored dynamically to dataset schema and data types.
   - Session history preservation, reset capabilities, and dataset version tracking.

2. **Deterministic Analytical Query Engine (Zero-Hallucination & Safe Execution)**:
   - Strict allowlist-based execution architecture that **never uses `eval()` or `exec()`**.
   - Supported analytical operations:
     - `count`, `distinct_count`, `sum`, `mean`, `median`, `min`, `max` aggregations.
     - Multi-column `group_by` with metric aggregations.
     - `sort_limit` (e.g. "Top 10 highest revenue companies", "Lowest price products").
     - Multi-condition safe `filter` expressions (`==`, `!=`, `>`, `<`, `>=`, `<=`, `contains`, `is_null`, `is_not_null`).
     - `outlier_detection` using standard statistical Interquartile Range (IQR, 1.5 * IQR bounds).
     - `correlation` analysis (Pearson linear correlation coefficient).
     - `distribution` frequency analysis.
     - `missing_analysis` for completeness audits.
   - Plan validation ensuring column existence, type safety, operation limits, and tenant data protection.

3. **Automated Multi-Dimensional Insights ("Auto Insights")**:
   - One-click automatic analytical scanning across multiple dimensions:
     - **Dataset Overview**: Total records, active columns, and overall data profile.
     - **Numerical Extremes**: Top & bottom extrema for numeric metrics.
     - **Categorical Distributions**: Dominant categories and concentration ratios.
     - **Statistical Outliers**: Anomaly detection highlighting extreme values and IQR boundaries.
     - **Correlations**: Notable linear associations with plain-language interpretations.
     - **Data Quality Alerts**: Missing value warnings and null-ratio flags.
   - Each insight card includes category badge, methodology explanation, supporting numerical evidence, and suggested follow-up questions.

4. **Statistical Analysis Module**:
   - Deep numeric profiling: `count`, `mean`, `std`, `min`, `25th percentile (Q1)`, `median (Q2)`, `75th percentile (Q3)`, `max`, `null_count`.
   - Full pairwise Pearson correlation matrix for numerical features.
   - Distribution metrics and statistical outlier boundary calculation.

5. **AI Chart Recommendations & Inline Visualizations**:
   - Automatically recommends and renders the optimal visualization for each query:
     - **Bar Charts**: Categorical rankings and group comparisons.
     - **Line Charts**: Chronological trends and sequential metrics.
     - **Area Charts**: Cumulative distributions and continuous metrics.
     - **Pie Charts**: Segment proportions and category shares.
     - **Histograms & Scatter Plots**: Distribution bins and relationship mapping.
   - Powered by Recharts with custom tooltips, legends, and responsive container scaling.

6. **Analysis Report Builder & Export**:
   - Generates standalone, responsive, styled executive HTML intelligence reports.
   - Reports include dataset version, executive summary, automated multi-dimensional insights, descriptive statistics tables, correlation matrices, outlier analysis, methodology notes, and custom user observations.
   - Secure download and local storage with tenant-isolated access controls.

---

## 🏗 Architecture & Tech Stack

### Frontend
- **Framework**: React 18 with Vite
- **Language**: TypeScript
- **Styling**: Tailwind CSS with custom SaaS light design system
- **Routing**: React Router v6 with public and protected routes
- **Server State**: TanStack Query (React Query) with optimistic cache invalidations & live polling
- **Visualizations**: Recharts for dynamic charts, histograms, quality gauges, and AI chat visualizations
- **Tables**: TanStack Table for dynamic schema rendering and inline editing
- **Markdown**: React-Markdown for AI chat responses and formatting
- **Icons**: Lucide React
- **HTTP Client**: Centralized Axios client with JWT interceptor & credentials

### Backend
- **Framework**: Python 3.11+ with FastAPI
- **Data Engineering & Analytics**: Pandas, NumPy, openpyxl
- **AI Query Planning & Insights**: Google Gemini SDK (`google-generativeai`), Groq SDK (`groq`), Deterministic Mock provider
- **AI Planning Graph**: LangGraph (`StateGraph`), LangChain Core
- **Search Adapter**: Tavily Search API client
- **Page Extractor**: Firecrawl API client + SSRF-safe URL sanitizer
- **Background Jobs**: Celery + Redis message broker & result backend
- **Validation & Deduplication**: Pydantic v2 with strict schemas + SHA256 deterministic hashing
- **ORM & Database**: SQLAlchemy 2.0 (Async) + PostgreSQL (with SQLite async support for testing)
- **Migrations**: Alembic with auto-discovery and versioned schema history (Migrations 001 - 005)
- **Security & Auth**: Argon2id password hashing (`argon2-cffi`), JWT bearer token authentication
- **Testing**: Pytest + pytest-asyncio + HTTPX AsyncClient (**48 automated integration tests**)

---

## 📁 Monorepo Project Structure

```
CodeCubicals/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/          # MetricCard, StatusBadge, ConfirmDialog, SearchBar, Pagination
│   │   │   ├── layout/          # AppLayout, Navbar, Sidebar, ProtectedRoute, PublicRoute
│   │   │   └── ui/              # Button, Input, Textarea, Select, Card, Modal, Badge, Spinner, EmptyState, Toast
│   │   ├── features/
│   │   │   ├── analysis/        # Phase 5 AI Insights & Reports UI
│   │   │   │   ├── DatasetInsightsTab.tsx  # Conversational Analyst Chat, Auto-Insights & Statistics Modals
│   │   │   │   └── DatasetReportsTab.tsx   # Executive Intelligence Reports & Standalone HTML Downloader
│   │   │   ├── auth/            # LoginForm, RegisterForm
│   │   │   ├── dashboard/       # RecentProjectsList, RecentDatasetsList, WorkflowRunsTable
│   │   │   ├── projects/        # ProjectCard, CreateProjectModal, EditProjectModal
│   │   │   ├── datasets/        # DatasetTable, DatasetDetailsModal, DatasetQualityTab, DataCleaningTab,
│   │   │   │                    # DataTransformationsTab, DuplicateResolverTab, DatasetAnalyticsTab,
│   │   │   │                    # VersionHistoryTab, ExportCenterModal, DatasetComparisonModal
│   │   │   ├── plans/           # CreatePlanModal, PlanViewer, PlanCard, EditableFieldBuilder, SearchQueryEditor
│   │   │   └── collection/      # StartCollectionModal, CollectionJobMonitor, DatasetRecordsTable, RecordProvenanceDrawer, DatasetSourcesList, DatasetOverviewCard
│   │   ├── hooks/               # useAuth, useProjects, useDatasets, usePlans, useCollection, useDatasetManagement, useAnalysis
│   │   ├── lib/                 # axios.ts, utils.ts
│   │   ├── services/            # authService, projectService, datasetService, planService, collectionService, datasetManagementService, analysisService
│   │   ├── types/               # auth, project, dataset, plan, collection, dataset_management, analysis
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
│   │   ├── analysis/            # Phase 5 AI Analytics & Query Engines
│   │   │   ├── query_planner.py    # Gemini NLP -> Structured Analytical Query Plan Model
│   │   │   ├── query_validator.py  # Strict Operation & Column Whitelist Validation
│   │   │   ├── query_executor.py   # Pure Pandas Analytical Query Execution & Chart Formatting
│   │   │   ├── insight_service.py  # Automated Multi-Dimensional Insight Generation
│   │   │   ├── statistics_service.py # Descriptive Stats, Pearson Correlations, IQR Outliers
│   │   │   └── report_service.py   # Standalone Styled HTML Report Generator
│   │   ├── datasets/            # Phase 4 Data Intelligence Core Engines
│   │   │   ├── profiling/       # profiler.py, quality_scorer.py
│   │   │   ├── cleaning/        # cleaning_service.py
│   │   │   ├── transformations/ # transformer.py (Safe AST Expression Evaluator)
│   │   │   ├── duplicates/      # dedup_resolver.py
│   │   │   ├── analytics/       # analytics_service.py
│   │   │   ├── comparison/      # comparator.py
│   │   │   └── export/          # export_service.py (CSV/XLSX/JSON + Formula Sanitization)
│   │   ├── ai/
│   │   │   ├── graphs/          # planning_graph.py (LangGraph 6-node StateGraph)
│   │   │   └── providers/       # base.py, gemini.py, groq.py, mock.py, __init__.py (Factory)
│   │   ├── collection/
│   │   │   ├── search/          # tavily_client.py (Tavily search adapter)
│   │   │   ├── extraction/      # firecrawl_client.py, structured_extractor.py
│   │   │   ├── processing/      # validator.py, deduplicator.py
│   │   │   ├── security/        # url_validator.py (SSRF protection)
│   │   │   ├── coordinator.py   # CollectionJobCoordinator (8-stage pipeline)
│   │   │   └── tasks.py         # Celery background tasks
│   │   ├── api/
│   │   │   ├── deps.py          # FastAPI auth & DB dependency injection
│   │   │   └── routes/          # auth, projects, datasets, plans, workflows, collection, dataset_management, analysis, dashboard
│   │   ├── core/                # config, celery_app, security (Argon2 + JWT), exceptions
│   │   ├── db/                  # session.py (AsyncSession), base.py
│   │   ├── models/              # User, Project, Dataset, CollectionPlan, CollectionJob, DatasetRecord, DataSource,
│   │   │                        # RecordSource, DatasetQualityReport, DatasetTransformation, DatasetVersion,
│   │   │                        # DatasetChart, DatasetMergeHistory, DatasetExport,
│   │   │                        # AnalysisSession, AnalysisMessage, AnalysisResult, AnalysisReport
│   │   ├── repositories/        # UserRepository, ProjectRepository, DatasetRepository, PlanRepository, CollectionRepository, DatasetManagementRepository, AnalysisRepository
│   │   ├── schemas/             # Pydantic v2 schemas for all models, plans, jobs, quality, cleaning, transformations, exports, analysis
│   │   ├── services/            # AuthService, ProjectService, DatasetService, PlanService, CollectionService, DatasetManagementService, AnalysisService
│   │   └── main.py              # FastAPI app lifecycle & router integration
│   ├── alembic/                 # Migration scripts (001_initial_schema to 005_ai_insights_and_analysis)
│   ├── tests/                   # Conftest & 48 comprehensive pytest async integration & unit tests
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

Key configuration parameters (see `.env.example`):

| Variable | Description | Default |
|---|---|---|
| `ENVIRONMENT` | Runtime environment (`development`, `production`) | `development` |
| `SECRET_KEY` | Secret key for JWT signing | `supersecretkey_change_in_production...` |
| `DATABASE_URL` | PostgreSQL async connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/data_intelligence_db` |
| `REDIS_URL` | Redis URL for caching & coordination | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery Redis broker URL | `redis://localhost:6379/1` |
| `CELERY_RESULT_BACKEND` | Celery Redis result backend | `redis://localhost:6379/2` |
| `AI_PROVIDER` | LLM provider (`gemini`, `groq`, `mock`) | `gemini` |
| `GEMINI_API_KEY` | Google Gemini API Key | `AIza...` |
| `GEMINI_MODEL` | Google Gemini Model Identifier | `gemini-1.5-pro` |
| `TAVILY_API_KEY` | Tavily Web Search API Key | `tvly-...` |
| `FIRECRAWL_API_KEY` | Firecrawl Web Extraction API Key | `fc-...` |
| `DATASET_MAX_RECORDS_FOR_SYNC` | Threshold for synchronous dataset processing | `5000` |
| `DATASET_PROFILE_BATCH_SIZE` | Profiler batch chunk size | `1000` |
| `DATASET_EXPORT_MAX_RECORDS` | Maximum export record limit | `100000` |
| `EXPORT_STORAGE_DIR` | Local disk storage directory for exports & HTML reports | `./storage/exports` |
| `EXPORT_FILE_RETENTION_HOURS` | Retention window for generated export files | `24` |
| `VITE_API_BASE_URL` | Frontend API backend URL | `http://localhost:8000` |

---

## 📡 Key API Endpoints (`/api/v1`)

| Method | Endpoint | Description |
|---|---|---|
| **Phase 5: AI Insights & Analysis** | | |
| `POST` | `/api/v1/datasets/{dataset_id}/analysis/chat` | Natural-language query -> Validated Pandas Plan -> Verified Answer + Chart |
| `GET` | `/api/v1/datasets/{dataset_id}/analysis/history` | List conversational messages and analytical results |
| `DELETE` | `/api/v1/datasets/{dataset_id}/analysis/history` | Clear analysis chat session history |
| `POST` | `/api/v1/datasets/{dataset_id}/analysis/insights` | Run automated multi-dimensional scan (extremes, segments, outliers, correlations) |
| `POST` | `/api/v1/datasets/{dataset_id}/analysis/statistics` | Comprehensive descriptive statistics and Pearson correlation matrix |
| `POST` | `/api/v1/datasets/{dataset_id}/analysis/reports` | Generate and persist an executive HTML/JSON intelligence report |
| `GET` | `/api/v1/datasets/{dataset_id}/analysis/reports` | List saved analysis reports for dataset |
| `GET` | `/api/v1/datasets/{dataset_id}/analysis/reports/{report_id}/download` | Securely download generated standalone HTML report |
| **Phase 4: Profiling & Quality** | | |
| `POST` | `/api/v1/datasets/{dataset_id}/profile` | Profile dataset and generate 5-dimension quality score |
| `GET` | `/api/v1/datasets/{dataset_id}/profile` | Get latest dataset profile and column statistics |
| `GET` | `/api/v1/datasets/{dataset_id}/quality-report` | Get detailed quality dimension scores and rule explanations |
| **Phase 4: Cleaning & Transformations** | | |
| `POST` | `/api/v1/datasets/{dataset_id}/clean/preview` | Preview before/after diff for a cleaning operation |
| `POST` | `/api/v1/datasets/{dataset_id}/clean/apply` | Apply cleaning operation with automatic version snapshot |
| `POST` | `/api/v1/datasets/{dataset_id}/transformations/preview` | Preview derived column or transformation on sample rows |
| `POST` | `/api/v1/datasets/{dataset_id}/transformations` | Execute transformation with safe AST allowlist |
| `GET` | `/api/v1/datasets/{dataset_id}/transformations` | List transformation history and executed operations |
| **Phase 4: Deduplication, Exports & Versions** | | |
| `GET` | `/api/v1/datasets/{dataset_id}/duplicates` | Detect duplicate record clusters by URL, hash, or composite key |
| `POST` | `/api/v1/datasets/{dataset_id}/duplicates/merge` | Merge duplicate cluster, retain winner, and preserve all source provenance |
| `POST` | `/api/v1/datasets/{dataset_id}/exports` | Generate CSV, Excel (`.xlsx`), or JSON export with formula protection |
| `GET` | `/api/v1/exports/{export_id}/download` | Securely download generated export workbook or file |
| `GET` | `/api/v1/datasets/{dataset_id}/versions` | List dataset version snapshots and change log |
| `POST` | `/api/v1/datasets/{dataset_id}/versions/{version_id}/restore` | Transactional rollback to a previous dataset version |

---

## 🚀 Quick Start with Docker Compose

```bash
docker-compose up --build
```

- **Frontend Application**: [http://localhost:5173](http://localhost:5173)
- **Backend API Docs (Swagger)**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- **Backend ReDoc**: [http://localhost:8000/api/v1/redoc](http://localhost:8000/api/v1/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 💻 Local Development Setup (Without Docker)

### 1. Prerequisites
Ensure **PostgreSQL** (port 5432) and **Redis** (port 6379) are running locally.

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# On Windows:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# Install dependencies (FastAPI, Pandas, openpyxl, Celery, LangGraph)
pip install -r requirements.txt

# Run Alembic migrations (001 -> 005)
alembic upgrade head

# Start FastAPI development server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 3. Start Celery Worker (In a separate terminal)

```bash
cd backend
.\venv\Scripts\Activate.ps1
celery -A app.core.celery_app.celery_app worker --loglevel=info --concurrency=3
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

Visit [http://localhost:5173](http://localhost:5173).

---

## 🧪 Automated Testing

### Backend Tests (Pytest)
Run the full automated test suite (48 comprehensive async integration, AI analysis, query execution, statistics, data quality, cleaning, transformations, export, and security tests):

```bash
cd backend
.\venv\Scripts\pytest.exe -v
```

**Test Suite Coverage (48/48 passing)**:
- **AI Query Planner & Validator**: Validates NLP translation, schema mapping, allowlist operation filters, limit clamping, and injection rejection.
- **Analytical Query Executor**: Verifies pure Pandas aggregations, group-bys, filtering, IQR outlier detection, Pearson correlations, and distributions.
- **Automated Insights & Statistics Engine**: Tests multi-dimensional insight generation and full descriptive statistical profiling.
- **Chat Query Flow & Report Generation**: Tests end-to-end question-to-answer workflow, chat history persistence, and standalone HTML report building.
- **Multi-Tenant Isolation**: Rigorously verifies that User B cannot query, inspect, view history, or download reports for User A's datasets.
- **Dataset Profiling, Cleaning, Transformations & Deduplication**: Complete test suite for Phase 1-4 capabilities.

### Frontend Build & Typecheck
```bash
cd frontend
npm run build
```

---

## 🔒 Security & Data Integrity Highlights

1. **Zero Hallucination Guarantee**: Answers to numerical questions are strictly computed using verified Pandas analytical routines over actual stored database records. The LLM is used solely to formulate structured query plans and explain calculated findings.
2. **Strict Query Sandbox (No `eval`/`exec`)**: The system rejects arbitrary Python execution. All operations are restricted to an explicit allowlist (`count`, `sum`, `mean`, `median`, `min`, `max`, `group_by`, `sort_limit`, `filter`, `outlier_detection`, `correlation`, `distribution`, `missing_analysis`).
3. **CSV Formula Injection Mitigation**: All spreadsheet exports inspect cells starting with `=`, `+`, `-`, `@`, `\t`, or `\r` and prefix them with `'` to neutralize remote command execution vulnerabilities.
4. **Safe Transformation Sandbox**: Derived column expressions are parsed into restricted AST operation trees with strict type checking.
5. **Non-Destructive Provenance Merging**: When duplicate records are merged, source references and verbatim evidence quotes from all duplicate records are preserved.
6. **Transactional Rollback Ledger**: Modifications automatically generate an immutable snapshot in `DatasetVersions` before writing changes.
7. **Multi-Tenant Isolation**: All datasets, analysis sessions, query results, exports, and reports enforce strict project and user ownership validation with `404 Not Found` for unauthorized tenants.
