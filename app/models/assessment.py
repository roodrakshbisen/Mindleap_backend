import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class SeverityLevel(str, enum.Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

class Assessment(Base):
    """E.g., PHQ-9 or GAD-7"""
    __tablename__ = "assessments"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    questions = relationship("Question", back_populates="assessment", cascade="all, delete-orphan", order_by="Question.order_num")

class Question(Base):
    __tablename__ = "assessment_questions"
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"))
    order_num = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    
    assessment = relationship("Assessment", back_populates="questions")
    answers = relationship("AnswerOption", back_populates="question", cascade="all, delete-orphan")

class AnswerOption(Base):
    __tablename__ = "assessment_options"
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("assessment_questions.id", ondelete="CASCADE"))
    text = Column(String(255), nullable=False)
    score_weight = Column(Integer, nullable=False) # E.g., 0, 1, 2, 3
    
    question = relationship("Question", back_populates="answers")

class AssessmentResult(Base):
    """The overarching result of a student taking a specific assessment."""
    __tablename__ = "assessment_results"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), index=True)
    total_score = Column(Integer, nullable=False)
    severity = Column(Enum(SeverityLevel), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    details = relationship("AssessmentResultDetail", back_populates="result", cascade="all, delete-orphan")
    __table_args__ = (Index('idx_assessment_student_time', 'student_id', 'created_at'),)

class AssessmentResultDetail(Base):
    """The individual answers chosen during that assessment instance."""
    __tablename__ = "assessment_result_details"
    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer, ForeignKey("assessment_results.id", ondelete="CASCADE"))
    question_id = Column(Integer, ForeignKey("assessment_questions.id"))
    selected_option_id = Column(Integer, ForeignKey("assessment_options.id"))
    
    result = relationship("AssessmentResult", back_populates="details")
