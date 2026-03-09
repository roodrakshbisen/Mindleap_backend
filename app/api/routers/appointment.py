from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.appointment import AppointmentStatus, Appointment as ApptModel
from app.schemas.appointment import (
    Appointment, AppointmentCreate, AppointmentUpdate, AppointmentReschedule,
    Availability, AvailabilityCreate
)
from app.services.appointment import AppointmentService, get_appointment_service

router = APIRouter()

# --- Availability Endpoints ---

@router.post("/availability", response_model=Availability, status_code=status.HTTP_201_CREATED)
def add_availability(
    data: AvailabilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
    appt_svc: AppointmentService = Depends(get_appointment_service)
) -> Any:
    """Counselors: Define structural open times."""
    if current_user.role != UserRole.COUNSELLOR:
        raise HTTPException(status_code=403, detail="Only counsellors can define availability.")
    return appt_svc.create_availability(current_user.id, data.start_time, data.end_time)

@router.get("/availability/{counsellor_id}", response_model=List[Availability])
def get_availability(
    counsellor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user), # Any authenticated user can check schedule
    appt_svc: AppointmentService = Depends(get_appointment_service)
) -> Any:
    """Fetch open time slots for a specific counselor."""
    return appt_svc.get_counsellor_availability(counsellor_id)

# --- Booking Endpoints ---

@router.post("/book", response_model=Appointment, status_code=status.HTTP_201_CREATED)
def book_session(
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
    appt_svc: AppointmentService = Depends(get_appointment_service)
) -> Any:
    """Students: Book an open slot."""
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can book sessions.")
    return appt_svc.book_appointment(current_user.id, data)

@router.get("/me", response_model=List[Appointment])
def my_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """Get all appointments for the logged-in user."""
    if current_user.role == UserRole.STUDENT:
        return db.query(ApptModel).filter(ApptModel.student_id == current_user.id).order_by(ApptModel.start_time).all()
    elif current_user.role == UserRole.COUNSELLOR:
        return db.query(ApptModel).filter(ApptModel.counsellor_id == current_user.id).order_by(ApptModel.start_time).all()
    return []

@router.patch("/{appointment_id}/transition", response_model=Appointment)
def transition_status(
    appointment_id: int,
    data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
    appt_svc: AppointmentService = Depends(get_appointment_service)
) -> Any:
    """Counselors: Complete/Confirm. Students/Counselors: Cancel."""
    return appt_svc.update_status(appointment_id, current_user, data)

@router.post("/{appointment_id}/reschedule", response_model=Appointment)
def reschedule_session(
    appointment_id: int,
    data: AppointmentReschedule,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
    appt_svc: AppointmentService = Depends(get_appointment_service)
) -> Any:
    """Students: Reschedule an existing appointment."""
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can reschedule via this endpoint.")
    return appt_svc.reschedule_appointment(appointment_id, current_user.id, data)
