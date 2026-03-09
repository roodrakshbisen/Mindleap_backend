from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User, UserRole
from app.schemas.assessment import Assessment as AssessmentSchema, AssessmentSubmit, AssessmentResult
from app.services.assessment import AssessmentService, get_assessment_service

router = APIRouter()

@router.get("/surveys", response_model=List[AssessmentSchema])
def get_available_assessments(
    current_user: User = Depends(deps.get_current_user),
    assessment_svc: AssessmentService = Depends(get_assessment_service)
) -> Any:
    """Fetch the structural definitions of all surveys (used to render UI forms)."""
    return assessment_svc.get_all_assessments()

@router.get("/surveys/{assessment_id}", response_model=AssessmentSchema)
def get_assessment_details(
    assessment_id: int,
    current_user: User = Depends(deps.get_current_user),
    assessment_svc: AssessmentService = Depends(get_assessment_service)
) -> Any:
    """Fetch a specific survey by ID."""
    return assessment_svc.get_assessment(assessment_id)

@router.post("/submit", response_model=AssessmentResult, status_code=status.HTTP_201_CREATED)
def submit_completed_assessment(
    payload: AssessmentSubmit,
    current_user: User = Depends(deps.get_current_user),
    assessment_svc: AssessmentService = Depends(get_assessment_service)
) -> Any:
    """
    Students Only: Submit a completed survey payload.
    The backend securely calculates the total score and logs the severity index.
    """
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can submit assessments.")
        
    return assessment_svc.submit_assessment(current_user.id, payload)

@router.get("/history", response_model=List[AssessmentResult])
def get_my_assessment_history(
    current_user: User = Depends(deps.get_current_user),
    assessment_svc: AssessmentService = Depends(get_assessment_service)
) -> Any:
    """Students Only: View historical scores and symptom severity changes over time."""
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can view their assessment history.")
    
    return assessment_svc.get_student_history(current_user.id)
