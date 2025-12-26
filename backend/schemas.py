from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    CANDIDATE = "candidate"

# Auth Schemas
class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.CANDIDATE

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: UserRole
    username: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[UserRole] = None

# Question Schemas
class QuestionBase(BaseModel):
    question_number: int
    question_text: str

class QuestionResponse(QuestionBase):
    id: int
    
    class Config:
        from_attributes = True

class QuestionWithAnswer(QuestionResponse):
    correct_answer: Optional[str] = None

# Answer Schemas
class AnswerSubmit(BaseModel):
    question_id: int
    answer_text: str

class SessionAnswersSubmit(BaseModel):
    session_id: int
    answers: List[AnswerSubmit]

# Test Session Schemas
class SessionStart(BaseModel):
    question_set_id: int

class SessionResponse(BaseModel):
    id: int
    candidate_id: int
    question_set_id: int
    started_at: datetime
    is_completed: bool
    
    class Config:
        from_attributes = True

# Question Set Schemas
class QuestionSetResponse(BaseModel):
    id: int
    title: str
    uploaded_at: datetime
    is_active: bool
    total_questions: int = 0
    
    class Config:
        from_attributes = True

class QuestionSetWithQuestions(QuestionSetResponse):
    questions: List[QuestionResponse]

# Result Schemas
class AnswerDetail(BaseModel):
    question_number: int
    question_text: str
    candidate_answer: str
    correct_answer: str
    is_correct: bool
    similarity_score: Optional[float] = None

class ResultResponse(BaseModel):
    id: int
    session_id: int
    total_questions: int
    correct_answers: int
    score_percentage: float
    passed: bool
    generated_at: datetime
    answer_details: List[AnswerDetail] = []
    
    class Config:
        from_attributes = True

# Admin Schemas
class CandidateResultSummary(BaseModel):
    candidate_username: str
    session_id: int
    submitted_at: Optional[datetime]
    score_percentage: float
    passed: bool
    total_questions: int
    correct_answers: int

# Upload Response
class UploadResponse(BaseModel):
    message: str
    question_set_id: Optional[int] = None
    total_questions: int = 0
