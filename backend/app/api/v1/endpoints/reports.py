from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.employee import Employee
from app.core.permissions import get_current_user
from app.schemas.reports import (
    CustomReportFilter,
    EnvironmentalReportData,
    SocialReportData,
    GovernanceReportData,
    ESGScoreSummary
)
from app.services.reports import (
    get_allowed_department_ids,
    get_environmental_report,
    get_social_report,
    get_governance_report,
    get_esg_summary_report,
    get_custom_report
)
from app.services.exports import (
    export_to_csv,
    export_to_xlsx,
    export_to_pdf
)

router = APIRouter()


@router.get("/environmental", response_model=EnvironmentalReportData, summary="Get Environmental Report")
async def read_environmental_report(
    department_id: Optional[int] = Query(None, description="Department ID filter"),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """
    Returns Environmental reporting metrics: total emissions, emissions by source type,
    environmental goals progress, and active product carbon footprint profiles.
    
    RBAC Scoping: Managers and Employees are silently restricted to their authorized departments.
    """
    allowed_ids = await get_allowed_department_ids(db, current_user, department_id)
    return await get_environmental_report(db, allowed_ids)


@router.get("/social", response_model=SocialReportData, summary="Get Social Report")
async def read_social_report(
    department_id: Optional[int] = Query(None, description="Department ID filter"),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """
    Returns Social pillar metrics: latest diversity metric segmentations, approved CSR stats,
    and employee training course completion rates.
    
    RBAC Scoping: Managers and Employees are silently restricted to their authorized departments.
    """
    allowed_ids = await get_allowed_department_ids(db, current_user, department_id)
    return await get_social_report(db, allowed_ids)


@router.get("/governance", response_model=GovernanceReportData, summary="Get Governance Report")
async def read_governance_report(
    department_id: Optional[int] = Query(None, description="Department ID filter"),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """
    Returns Governance pillar metrics: active policy acknowledgement rates, department audits,
    and open compliance/risk summary counts by severity.
    
    RBAC Scoping: Managers and Employees are silently restricted to their authorized departments.
    """
    allowed_ids = await get_allowed_department_ids(db, current_user, department_id)
    return await get_governance_report(db, allowed_ids)


@router.get("/esg-summary", response_model=ESGScoreSummary, summary="Get Executive ESG Scores Summary")
async def read_esg_summary_report(
    department_id: Optional[int] = Query(None, description="Department ID filter"),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """
    Executive overview displaying scores (Environmental, Social, Governance, Total Score)
    and a department-by-department score comparison matrix.
    
    RBAC Scoping: Managers and Employees are silently restricted to their authorized departments.
    """
    allowed_ids = await get_allowed_department_ids(db, current_user, department_id)
    return await get_esg_summary_report(db, allowed_ids)


@router.post("/custom", summary="Custom Report Builder & Exporter")
async def custom_report_builder(
    filter_payload: CustomReportFilter,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """
    Accepts filter payload parameters (dates, module, employee, challenge, etc.)
    and handles two actions:
    1. Runs the report dynamically and returns structured JSON (for in-app UI preview)
    2. Exports styled, downloadable documents (PDF, Excel XLSX, or CSV) based on export_format.
    
    RBAC Scoping: Managers and Employees are silently restricted to their authorized department tree scope.
    """
    allowed_ids = await get_allowed_department_ids(db, current_user, filter_payload.department_id)
    
    # Generate the custom report data dictionary
    report_data = await get_custom_report(db, allowed_ids, filter_payload.model_dump())

    fmt = filter_payload.export_format.lower() if filter_payload.export_format else "json"
    filename = f"ecosphere_report_{date.today()}"

    if fmt == "json":
        return report_data
    elif fmt == "csv":
        return export_to_csv(report_data, f"{filename}.csv")
    elif fmt == "xlsx":
        return export_to_xlsx(report_data, f"{filename}.xlsx")
    elif fmt == "pdf":
        return export_to_pdf(report_data, f"{filename}.pdf")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format '{filter_payload.export_format}'. Supported: json, csv, xlsx, pdf"
        )
