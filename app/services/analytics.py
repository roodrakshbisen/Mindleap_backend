from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.appointment import Appointment, AppointmentStatus
from app.models.chat import ChatSession, PeerMessage
# If assessment models were implemented in code they would be imported here
# from app.models.assessment import AssessmentResult

from app.schemas.analytics import AdminDashboardAnalytics, EngagementStats, MentalHealthIndex

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_metrics(self) -> AdminDashboardAnalytics:
        """
        Aggregates data across the platform for University Admins.
        In production, this would be heavily cached or calculated via 
        asynchronous Celery workers overnight.
        """
        
        # 1. Appointments Data
        total_appts = self.db.query(Appointment).count()
        completed_appts = self.db.query(Appointment).filter(Appointment.status == AppointmentStatus.COMPLETED).count()
        canceled_appts = self.db.query(Appointment).filter(Appointment.status == AppointmentStatus.CANCELED).count()
        
        # 2. Chat Data
        active_bots = self.db.query(ChatSession).filter(ChatSession.is_active == True).count()
        peer_msgs_count = self.db.query(PeerMessage).count()
        
        engagement = EngagementStats(
            total_appointments=total_appts,
            completed_appointments=completed_appts,
            canceled_appointments=canceled_appts,
            active_chat_sessions=active_bots,
            total_peer_messages_sent=peer_msgs_count
        )

        # 3. Mental Health / Stress Scores (Mocked calculation since Assessments aren't fully wired)
        # In reality: SELECT department_id, AVG(total_score) FROM assessment_results GROUP BY department_id
        mock_department_data = [
            MentalHealthIndex(department_name="Computer Science", average_score=7.2, total_students_assessed=450),
            MentalHealthIndex(department_name="Business", average_score=5.8, total_students_assessed=320),
            MentalHealthIndex(department_name="Nursing", average_score=8.1, total_students_assessed=210)
        ]
        
        return AdminDashboardAnalytics(
            overall_stress_score=6.8, # Mocked calculated average
            department_indices=mock_department_data,
            engagement=engagement
        )

from fastapi import Depends
from app.db.database import get_db

def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)
