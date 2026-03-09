from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from app.models.appointment import AppointmentStatus

# --- Availability Schemas ---
class AvailabilityBase(BaseModel):
    start_time: datetime
    end_time: datetime

class AvailabilityCreate(AvailabilityBase):
    pass

class Availability(AvailabilityBase):
    id: int
    counsellor_id: int
    is_booked: bool

    class Config:
        from_attributes = True

# --- Appointment Schemas ---
class AppointmentBase(BaseModel):
    counsellor_id: int
    start_time: datetime
    end_time: datetime
    reason_for_visit: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    """Payload to book an appointment."""
    availability_id: int

class AppointmentUpdate(BaseModel):
    """Used for counselors or students transitioning state (e.g., CANCELED, CONFIRMED)"""
    status: Optional[AppointmentStatus] = None
    cancellation_reason: Optional[str] = None
    counsellor_notes: Optional[str] = None
    meeting_link: Optional[str] = None

class AppointmentReschedule(BaseModel):
    """Payload specifically for rescheduling."""
    new_availability_id: int
    new_start_time: datetime
    new_end_time: datetime
    reason: Optional[str] = None

class Appointment(AppointmentBase):
    id: int
    student_id: int
    availability_id: Optional[int]
    status: AppointmentStatus
    counsellor_notes: Optional[str]
    cancellation_reason: Optional[str]
    meeting_link: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
