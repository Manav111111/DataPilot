from fastapi import APIRouter
from app.api.routes.auth import router as auth_router
from app.api.routes.projects import router as projects_router
from app.api.routes.datasets import router as datasets_router
from app.api.routes.workflows import router as workflows_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.plans import router as plans_router
from app.api.routes.collection import router as collection_router
from app.api.routes.dataset_management import router as dataset_management_router
from app.api.routes.analysis import router as analysis_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(datasets_router)
api_router.include_router(workflows_router)
api_router.include_router(dashboard_router)
api_router.include_router(plans_router)
api_router.include_router(collection_router)
api_router.include_router(dataset_management_router)
api_router.include_router(analysis_router)

