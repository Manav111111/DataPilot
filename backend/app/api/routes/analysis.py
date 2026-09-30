from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.analysis_service import AnalysisService
from app.schemas.analysis import (
    ChatQueryRequest,
    ChatQueryResponse,
    AnalysisSessionRead,
    AutoInsightsResponse,
    StatisticalAnalysisResponse,
    ReportCreateRequest,
    AnalysisReportRead,
)
from app.schemas.common import MessageResponse

router = APIRouter()


@router.post(
    "/datasets/{dataset_id}/analysis/chat",
    response_model=ChatQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a natural-language question about the dataset",
)
async def chat_with_dataset(
    dataset_id: str,
    req: ChatQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AnalysisService(db)
    return await service.execute_chat_query(
        dataset_id=dataset_id,
        user_id=str(current_user.id),
        message=req.message,
        session_id=req.session_id,
    )


@router.get(
    "/datasets/{dataset_id}/analysis/sessions",
    response_model=List[AnalysisSessionRead],
    summary="List analysis chat sessions for a dataset",
)
async def list_analysis_sessions(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AnalysisService(db)
    return await service.list_sessions(dataset_id=dataset_id, user_id=str(current_user.id))


@router.get(
    "/datasets/{dataset_id}/analysis/sessions/{session_id}",
    response_model=AnalysisSessionRead,
    summary="Get full history of an analysis chat session",
)
async def get_analysis_session(
    dataset_id: str,
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AnalysisService(db)
    return await service.get_session(session_id=session_id, user_id=str(current_user.id))


@router.delete(
    "/datasets/{dataset_id}/analysis/sessions/{session_id}",
    response_model=MessageResponse,
    summary="Delete an analysis chat session",
)
async def delete_analysis_session(
    dataset_id: str,
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AnalysisService(db)
    await service.delete_session(session_id=session_id, user_id=str(current_user.id))
    return MessageResponse(message="Analysis session deleted successfully.")


@router.post(
    "/datasets/{dataset_id}/analysis/insights",
    response_model=AutoInsightsResponse,
    summary="Generate automated multi-dimensional dataset insights",
)
async def generate_dataset_insights(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AnalysisService(db)
    return await service.get_auto_insights(dataset_id=dataset_id, user_id=str(current_user.id))


@router.post(
    "/datasets/{dataset_id}/analysis/statistics",
    response_model=StatisticalAnalysisResponse,
    summary="Generate statistical analysis (descriptive, correlation, outliers)",
)
async def generate_dataset_statistics(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AnalysisService(db)
    return await service.get_statistics(dataset_id=dataset_id, user_id=str(current_user.id))


@router.post(
    "/datasets/{dataset_id}/analysis/reports",
    response_model=AnalysisReportRead,
    status_code=status.HTTP_201_CREATED,
    summary="Generate and save an analysis report",
)
async def create_analysis_report(
    dataset_id: str,
    req: ReportCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AnalysisService(db)
    return await service.create_report(
        dataset_id=dataset_id, user_id=str(current_user.id), req=req
    )


@router.get(
    "/datasets/{dataset_id}/analysis/reports",
    response_model=List[AnalysisReportRead],
    summary="List saved analysis reports for dataset",
)
async def list_analysis_reports(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AnalysisService(db)
    return await service.list_reports(dataset_id=dataset_id, user_id=str(current_user.id))


@router.get(
    "/analysis/reports/{report_id}/download",
    summary="Download generated analysis report HTML file",
)
async def download_analysis_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AnalysisService(db)
    file_path, title = await service.get_report_download(
        report_id=report_id, user_id=str(current_user.id)
    )
    safe_filename = f"{title.lower().replace(' ', '_')}.html"
    return FileResponse(
        path=file_path,
        media_type="text/html",
        filename=safe_filename,
    )
