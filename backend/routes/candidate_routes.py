from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserRole, QuestionSet, Question, AnswerKey, TestSession, Result, CandidateAnswer
from schemas import (
    SessionStart, SessionResponse, QuestionResponse, 
    SessionAnswersSubmit, ResultResponse, AnswerDetail, QuestionSetResponse
)
from auth import decode_token
from services.grading import GradingService
from typing import List

router = APIRouter(prefix="/api/candidate", tags=["candidate"])
security = HTTPBearer()

def get_current_candidate(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Dependency to verify candidate authentication"""
    token_data = decode_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user = db.query(User).filter(User.username == token_data.username).first()
    if not user or user.role != UserRole.CANDIDATE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Candidate access required"
        )
    
    return user

@router.get("/question-sets", response_model=List[QuestionSetResponse])
def get_available_question_sets(
    current_candidate: User = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Get all available question sets"""
    question_sets = db.query(QuestionSet).filter(QuestionSet.is_active == True).all()
    
    result = []
    for qs in question_sets:
        question_count = db.query(Question).filter(Question.question_set_id == qs.id).count()
        result.append({
            "id": qs.id,
            "title": qs.title,
            "uploaded_at": qs.uploaded_at,
            "is_active": qs.is_active,
            "total_questions": question_count
        })
    
    return result

@router.post("/session/start", response_model=SessionResponse)
def start_test_session(
    session_data: SessionStart,
    current_candidate: User = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Start a new test session"""
    # Check if question set exists and is active
    question_set = db.query(QuestionSet).filter(
        QuestionSet.id == session_data.question_set_id,
        QuestionSet.is_active == True
    ).first()
    
    if not question_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question set not found or inactive"
        )
    
    # Check if user already has an incomplete session
    existing_session = db.query(TestSession).filter(
        TestSession.candidate_id == current_candidate.id,
        TestSession.question_set_id == session_data.question_set_id,
        TestSession.is_completed == False
    ).first()
    
    if existing_session:
        return existing_session
    
    # Create new session
    new_session = TestSession(
        candidate_id=current_candidate.id,
        question_set_id=session_data.question_set_id,
        is_completed=False
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return new_session

@router.get("/test/{session_id}", response_model=List[QuestionResponse])
def get_test_questions(
    session_id: int,
    current_candidate: User = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Get all questions for a test session"""
    # Verify session belongs to current candidate
    session = db.query(TestSession).filter(
        TestSession.id == session_id,
        TestSession.candidate_id == current_candidate.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session already completed"
        )
    
    # Get questions
    questions = db.query(Question).filter(
        Question.question_set_id == session.question_set_id
    ).order_by(Question.question_number).all()
    
    return questions

@router.post("/submit", response_model=ResultResponse)
def submit_test(
    submission: SessionAnswersSubmit,
    current_candidate: User = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Submit test answers and get results"""
    # Verify session belongs to current candidate
    session = db.query(TestSession).filter(
        TestSession.id == submission.session_id,
        TestSession.candidate_id == current_candidate.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session already completed"
        )
    
    # Get all questions and their answer keys
    questions = db.query(Question).filter(
        Question.question_set_id == session.question_set_id
    ).all()
    
    question_map = {q.id: q for q in questions}
    
    # Get correct answers
    correct_answers_map = {}
    for question in questions:
        answer_key = db.query(AnswerKey).filter(AnswerKey.question_id == question.id).first()
        if answer_key:
            correct_answers_map[question.question_number] = answer_key.correct_answer
    
    # Save candidate answers
    candidate_answers_data = []
    for answer in submission.answers:
        if answer.question_id not in question_map:
            continue
        
        question_num = question_map[answer.question_id].question_number
        
        candidate_answer = CandidateAnswer(
            session_id=session.id,
            question_id=answer.question_id,
            answer_text=answer.answer_text
        )
        db.add(candidate_answer)
        
        candidate_answers_data.append({
            "question_number": question_num,
            "answer_text": answer.answer_text
        })
    
    # Grade the test using fuzzy matching
    grading_result = GradingService.grade_test(
        candidate_answers_data,
        correct_answers_map,
        method="fuzzy",
        threshold=0.75,
        passing_percentage=60.0
    )
    
    # Update candidate answers with grading results
    for graded in grading_result["graded_answers"]:
        answer = db.query(CandidateAnswer).filter(
            CandidateAnswer.session_id == session.id,
            CandidateAnswer.question_id == db.query(Question).filter(
                Question.question_set_id == session.question_set_id,
                Question.question_number == graded["question_number"]
            ).first().id
        ).first()
        
        if answer:
            answer.is_correct = graded["is_correct"]
            answer.similarity_score = graded["similarity_score"]
    
    # Create result record
    result = Result(
        session_id=session.id,
        total_questions=grading_result["total_questions"],
        correct_answers=grading_result["correct_answers"],
        score_percentage=grading_result["score_percentage"],
        passed=grading_result["passed"]
    )
    db.add(result)
    
    # Mark session as completed
    session.is_completed = True
    from datetime import datetime
    session.submitted_at = datetime.utcnow()
    
    db.commit()
    db.refresh(result)
    
    # Prepare detailed answer feedback
    answer_details = []
    for graded in grading_result["graded_answers"]:
        answer_details.append({
            "question_number": graded["question_number"],
            "question_text": db.query(Question).filter(
                Question.question_set_id == session.question_set_id,
                Question.question_number == graded["question_number"]
            ).first().question_text,
            "candidate_answer": graded["candidate_answer"],
            "correct_answer": graded["correct_answer"],
            "is_correct": graded["is_correct"],
            "similarity_score": graded["similarity_score"]
        })
    
    return {
        "id": result.id,
        "session_id": result.session_id,
        "total_questions": result.total_questions,
        "correct_answers": result.correct_answers,
        "score_percentage": result.score_percentage,
        "passed": result.passed,
        "generated_at": result.generated_at,
        "answer_details": answer_details
    }

@router.get("/result/{session_id}", response_model=ResultResponse)
def get_result(
    session_id: int,
    current_candidate: User = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Get result for a completed session"""
    # Verify session belongs to current candidate
    session = db.query(TestSession).filter(
        TestSession.id == session_id,
        TestSession.candidate_id == current_candidate.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if not session.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session not yet completed"
        )
    
    result = db.query(Result).filter(Result.session_id == session_id).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found"
        )
    
    # Get detailed answer feedback
    candidate_answers = db.query(CandidateAnswer).filter(
        CandidateAnswer.session_id == session_id
    ).all()
    
    answer_details = []
    for ca in candidate_answers:
        question = db.query(Question).filter(Question.id == ca.question_id).first()
        answer_key = db.query(AnswerKey).filter(AnswerKey.question_id == ca.question_id).first()
        
        answer_details.append({
            "question_number": question.question_number,
            "question_text": question.question_text,
            "candidate_answer": ca.answer_text,
            "correct_answer": answer_key.correct_answer if answer_key else "N/A",
            "is_correct": ca.is_correct,
            "similarity_score": ca.similarity_score
        })
    
    # Sort by question number
    answer_details.sort(key=lambda x: x["question_number"])
    
    return {
        "id": result.id,
        "session_id": result.session_id,
        "total_questions": result.total_questions,
        "correct_answers": result.correct_answers,
        "score_percentage": result.score_percentage,
        "passed": result.passed,
        "generated_at": result.generated_at,
        "answer_details": answer_details
    }
