from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.models.assessment import SeverityLevel

# --- Options & Questions (Read-Only structurally for now) ---
class AnswerOptionBase(BaseModel):
    text: str
    score_weight: int

class AnswerOption(AnswerOptionBase):
    id: int
    question_id: int
    class Config:
        from_attributes = True

class QuestionBase(BaseModel):
    order_num: int
    text: str

class Question(QuestionBase):
    id: int
    assessment_id: int
    answers: List[AnswerOption] = []
    class Config:
        from_attributes = True

class AssessmentBase(BaseModel):
    title: str
    description: Optional[str] = None

class Assessment(AssessmentBase):
    id: int
    questions: List[Question] = []
    class Config:
        from_attributes = True

# --- Submission Payloads ---
class AssessmentSubmissionDetail(BaseModel):
    question_id: int
    selected_option_id: int

class AssessmentSubmit(BaseModel):
    """Payload sent by the frontend when a student completes a survey."""
    assessment_id: int
    answers: List[AssessmentSubmissionDetail]

# --- Results ---
class AssessmentResultDetail(BaseModel):
    id: int
    question_id: int
    selected_option_id: int
    class Config:
        from_attributes = True

class AssessmentResultBase(BaseModel):
    total_score: int
    severity: Optional[SeverityLevel]
    assessment_id: int

class AssessmentResult(AssessmentResultBase):
    id: int
    student_id: int
    created_at: datetime
    details: List[AssessmentResultDetail] = []
    class Config:
        from_attributes = True
