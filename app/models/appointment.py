import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class AppointmentStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELED = "canceled"
    COMPLETED = "completed"

class CounsellorAvailability(Base):
    """Time slots defined by a counsellor."""
    __tablename__ = "counsellor_availability"
    id = Column(Integer, primary_key=True, index=True)
    counsellor_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    is_booked = Column(Boolean, default=False)
    
    __table_args__ = (Index('idx_counsellor_time', 'counsellor_id', 'start_time'),)

class Appointment(Base):
    """A booked session between a student and counsellor."""
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    counsellor_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    availability_id = Column(Integer, ForeignKey("counsellor_availability.id", ondelete="SET NULL"), nullable=True)
    
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    
    status = Column(Enum(AppointmentStatus, name="appointmentstatus", native_enum=True), default=AppointmentStatus.PENDING, index=True)
    
    # Counsellor's private notes after the session
    counsellor_notes = Column(Text, nullable=True)
    
    # Why the student booked or canceled
    reason_for_visit = Column(Text, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    
    meeting_link = Column(String(255), nullable=True) # E.g., Zoom/Google Meet
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_appt_student_time', 'student_id', 'start_time'),
        Index('idx_appt_counsellor_time', 'counsellor_id', 'start_time'),
    )
