from typing import Optional, Dict
from pydantic import BaseModel

class MentalHealthIndex(BaseModel):
    department_name: str
    average_score: float
    total_students_assessed: int

class EngagementStats(BaseModel):
    total_appointments: int
    completed_appointments: int
    canceled_appointments: int
    active_chat_sessions: int
    total_peer_messages_sent: int

class ResourceUsageStats(BaseModel):
    top_categories: Dict[str, int] # e.g. {"Anxiety": 450, "Depression": 320}
    total_resources_viewed: int

class AdminDashboardAnalytics(BaseModel):
    overall_stress_score: float # 1-10 Scale
    department_indices: list[MentalHealthIndex]
    engagement: EngagementStats
    # resource_usage: ResourceUsageStats # Implement when Content Module is built
