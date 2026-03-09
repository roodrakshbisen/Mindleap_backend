from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.db.database import get_db
from app.models.user import User
from app.schemas.analytics import AdminDashboardAnalytics
from app.services.analytics import AnalyticsService, get_analytics_service

router = APIRouter()

@router.get("/dashboard", response_model=AdminDashboardAnalytics)
def get_admin_dashboard(
    db: Session = Depends(get_db),
    # Require strictly an admin user via RBAC dependency
    current_admin: User = Depends(deps.get_current_active_admin), 
    analytics_svc: AnalyticsService = Depends(get_analytics_service)
) -> Any:
    """
    University Administrators Only: Fetch aggregated mental health platform statistics.
    """
    return analytics_svc.get_dashboard_metrics()
