from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    CANDIDATE = "candidate"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    test_sessions = relationship("TestSession", back_populates="candidate")

class QuestionSet(Base):
    __tablename__ = "question_sets"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    pdf_filename = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    questions = relationship("Question", back_populates="question_set", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    question_set_id = Column(Integer, ForeignKey("question_sets.id"), nullable=False)
    question_number = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    
    # Relationships
    question_set = relationship("QuestionSet", back_populates="questions")
    answer_key = relationship("AnswerKey", back_populates="question", uselist=False, cascade="all, delete-orphan")
    candidate_answers = relationship("CandidateAnswer", back_populates="question", cascade="all, delete-orphan")

class AnswerKey(Base):
    __tablename__ = "answer_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, unique=True)
    correct_answer = Column(Text, nullable=False)
    pdf_filename = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    question = relationship("Question", back_populates="answer_key")

class TestSession(Base):
    __tablename__ = "test_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_set_id = Column(Integer, ForeignKey("question_sets.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)
    
    # Candidate Details (Pre-test form)
    candidate_name = Column(String, nullable=True)
    candidate_email = Column(String, nullable=True)
    candidate_mobile = Column(String, nullable=True)
    test_date = Column(String, nullable=True)  # Stored as string for flexibility
    batch_time = Column(String, nullable=True)
    
    # Relationships
    candidate = relationship("User", back_populates="test_sessions")
    question_set = relationship("QuestionSet")
    answers = relationship("CandidateAnswer", back_populates="session", cascade="all, delete-orphan")
    result = relationship("Result", back_populates="session", uselist=False)

class CandidateAnswer(Base):
    __tablename__ = "candidate_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("test_sessions.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    answer_text = Column(Text, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    
    # Grading results
    is_correct = Column(Boolean, nullable=True)
    similarity_score = Column(Float, nullable=True)  # For fuzzy matching
    
    # Relationships
    session = relationship("TestSession", back_populates="answers")
    question = relationship("Question", back_populates="candidate_answers")

class Result(Base):
    __tablename__ = "results"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("test_sessions.id"), nullable=False, unique=True)
    total_questions = Column(Integer, nullable=False)
    correct_answers = Column(Integer, nullable=False)
    score_percentage = Column(Float, nullable=False)
    passed = Column(Boolean, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("TestSession", back_populates="result")
