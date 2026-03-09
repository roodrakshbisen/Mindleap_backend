from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.appointment import Appointment, CounsellorAvailability, AppointmentStatus
from app.models.user import User, UserRole
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate, AppointmentReschedule

class AppointmentService:
    def __init__(self, db: Session):
        self.db = db

    # --- Counsellor Availability ---
    
    def create_availability(self, counsellor_id: int, start_time: datetime, end_time: datetime) -> CounsellorAvailability:
        # Check if counselor already has overlapping availability
        overlap = self.db.query(CounsellorAvailability).filter(
            CounsellorAvailability.counsellor_id == counsellor_id,
            CounsellorAvailability.start_time < end_time,
            CounsellorAvailability.end_time > start_time
        ).first()
        
        if overlap:
            raise HTTPException(status_code=400, detail="Availability slot overlaps with an existing one.")
            
        avail = CounsellorAvailability(
            counsellor_id=counsellor_id,
            start_time=start_time,
            end_time=end_time
        )
        self.db.add(avail)
        self.db.commit()
        self.db.refresh(avail)
        return avail

    def get_counsellor_availability(self, counsellor_id: int) -> List[CounsellorAvailability]:
        return self.db.query(CounsellorAvailability).filter(
            CounsellorAvailability.counsellor_id == counsellor_id,
            CounsellorAvailability.is_booked == False,
            CounsellorAvailability.start_time > datetime.utcnow() # Only future slots
        ).order_by(CounsellorAvailability.start_time).all()

    # --- Appointments ---

    def book_appointment(self, student_id: int, data: AppointmentCreate) -> Appointment:
        # 1. Verify availability exists and is open
        avail = self.db.query(CounsellorAvailability).filter(
            CounsellorAvailability.id == data.availability_id,
            CounsellorAvailability.counsellor_id == data.counsellor_id
        ).with_for_update().first() # Row-level lock to prevent concurrent double bookings

        if not avail or avail.is_booked:
            raise HTTPException(status_code=400, detail="This time slot is no longer available.")
            
        # 2. Verify student doesn't already have an appointment at this exact time
        student_conflict = self.db.query(Appointment).filter(
            Appointment.student_id == student_id,
            Appointment.start_time < data.end_time,
            Appointment.end_time > data.start_time,
            Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED])
        ).first()

        if student_conflict:
            self.db.rollback() # Release the lock if we fail here
            raise HTTPException(status_code=400, detail="You already have an appointment booked during this time.")

        # 3. Create appointment and mark slot as booked
        avail.is_booked = True
        appt = Appointment(
            student_id=student_id,
            **data.dict()
        )
        self.db.add(appt)
        self.db.commit()
        self.db.refresh(appt)
        return appt

    def update_status(self, appointment_id: int, user: User, data: AppointmentUpdate) -> Appointment:
        appt = self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appt:
            raise HTTPException(status_code=404, detail="Appointment not found")

        # Permissions check
        if user.role == UserRole.STUDENT and appt.student_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        if user.role == UserRole.COUNSELLOR and appt.counsellor_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        old_status = appt.status

        # Update fields
        for key, value in data.dict(exclude_unset=True).items():
            setattr(appt, key, value)

        # Handle freeing up the availability slot if canceled
        if data.status == AppointmentStatus.CANCELED and old_status != AppointmentStatus.CANCELED:
            if appt.availability_id:
                avail = self.db.query(CounsellorAvailability).filter(CounsellorAvailability.id == appt.availability_id).first()
                if avail:
                    avail.is_booked = False

        self.db.commit()
        self.db.refresh(appt)
        return appt

    def reschedule_appointment(self, appointment_id: int, student_id: int, data: AppointmentReschedule) -> Appointment:
        appt = self.db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.student_id == student_id
        ).first()
        
        if not appt or appt.status in [AppointmentStatus.CANCELED, AppointmentStatus.COMPLETED]:
            raise HTTPException(status_code=400, detail="Cannot reschedule this appointment.")

        # 1. Lock the NEW availability slot
        new_avail = self.db.query(CounsellorAvailability).filter(
            CounsellorAvailability.id == data.new_availability_id,
            CounsellorAvailability.counsellor_id == appt.counsellor_id
        ).with_for_update().first()

        if not new_avail or new_avail.is_booked:
            raise HTTPException(status_code=400, detail="The new time slot is not available.")

        # 2. Free the OLD availability slot
        if appt.availability_id:
            old_avail = self.db.query(CounsellorAvailability).filter(CounsellorAvailability.id == appt.availability_id).first()
            if old_avail:
                old_avail.is_booked = False

        # 3. Update appointment
        new_avail.is_booked = True
        appt.availability_id = data.new_availability_id
        appt.start_time = data.new_start_time
        appt.end_time = data.new_end_time
        if data.reason:
            appt.reason_for_visit = f"{appt.reason_for_visit}\n[Rescheduled: {data.reason}]"

        self.db.commit()
        self.db.refresh(appt)
        return appt

from fastapi import Depends
from app.db.database import get_db

def get_appointment_service(db: Session = Depends(get_db)) -> AppointmentService:
    return AppointmentService(db)
