from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.assessment import (
    Assessment, Question, AnswerOption, AssessmentResult, 
    AssessmentResultDetail, SeverityLevel
)
from app.schemas.assessment import AssessmentSubmit

class AssessmentService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_assessments(self) -> List[Assessment]:
        """Fetch all available surveys (e.g., PHQ-9, GAD-7) with nested questions and options."""
        return self.db.query(Assessment).all()

    def get_assessment(self, assessment_id: int) -> Assessment:
        appt = self.db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if not appt:
            raise HTTPException(status_code=404, detail="Assessment not found.")
        return appt

    def get_student_history(self, student_id: int) -> List[AssessmentResult]:
        """Fetch all past assessment results for a specific student."""
        return self.db.query(AssessmentResult).filter(
            AssessmentResult.student_id == student_id
        ).order_by(AssessmentResult.created_at.desc()).all()

    def submit_assessment(self, student_id: int, payload: AssessmentSubmit) -> AssessmentResult:
        """
        Validates the submission against the database, calculates the total score 
        based on the defined option weights, and determines severity.
        """
        assessment = self.get_assessment(payload.assessment_id)
        
        # 1. Fetch valid questions and options into a quick-lookup dictionary
        valid_question_ids = {q.id for q in assessment.questions}
        option_weights = {} # mapping option_id -> score
        
        for q in assessment.questions:
            for opt in q.answers:
                option_weights[opt.id] = opt.score_weight

        # 2. Score the submission
        total_score = 0
        details_to_insert = []
        
        # Keep track to ensure all questions were answered exactly once
        answered_questions = set()

        for answer in payload.answers:
            if answer.question_id not in valid_question_ids:
                raise HTTPException(status_code=400, detail=f"Question ID {answer.question_id} does not belong to this assessment.")
                
            if answer.selected_option_id not in option_weights:
                raise HTTPException(status_code=400, detail=f"Invalid option ID {answer.selected_option_id} for Question {answer.question_id}.")
                
            if answer.question_id in answered_questions:
                raise HTTPException(status_code=400, detail=f"Duplicate answer for Question ID {answer.question_id}.")
                
            answered_questions.add(answer.question_id)
            total_score += option_weights[answer.selected_option_id]
            
            details_to_insert.append(AssessmentResultDetail(
                question_id=answer.question_id,
                selected_option_id=answer.selected_option_id
            ))
            
        # Ensure the student didn't skip anything
        if len(answered_questions) != len(valid_question_ids):
            raise HTTPException(status_code=400, detail="Incomplete assessment submitted. Please answer all questions.")

        # 3. Calculate Severity (Example logic based roughly on standard PHQ-9 thresholds)
        severity = SeverityLevel.LOW
        if total_score >= 20:
            severity = SeverityLevel.CRITICAL
        elif total_score >= 15:
            severity = SeverityLevel.HIGH
        elif total_score >= 10:
            severity = SeverityLevel.MODERATE
            
        # 4. Save the Result Wrapper
        result = AssessmentResult(
            student_id=student_id,
            assessment_id=assessment.id,
            total_score=total_score,
            severity=severity
        )
        self.db.add(result)
        self.db.commit() # Commit to get the result.id
        self.db.refresh(result)
        
        # 5. Save the Individual Detail Items
        for detail in details_to_insert:
            detail.result_id = result.id
            self.db.add(detail)
            
        self.db.commit()
        return result


from fastapi import Depends
from app.db.database import get_db

def get_assessment_service(db: Session = Depends(get_db)) -> AssessmentService:
    return AssessmentService(db)
