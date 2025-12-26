from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserRole, QuestionSet, Question, AnswerKey, TestSession, Result, CandidateAnswer
from schemas import (
    UploadResponse, QuestionSetResponse, QuestionWithAnswer, 
    CandidateResultSummary, ResultResponse, AnswerDetail
)
from auth import decode_token
from services.pdf_parser import PDFParser
import os
import shutil
from typing import List
from datetime import datetime

router = APIRouter(prefix="/api/admin", tags=["admin"])
security = HTTPBearer()

def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Dependency to verify admin authentication"""
    token_data = decode_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user = db.query(User).filter(User.username == token_data.username).first()
    if not user or user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return user

@router.post("/upload/questions", response_model=UploadResponse)
async def upload_questions(
    file: UploadFile = File(...),
    title: str = Form(...),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Upload and parse question PDF"""
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    # Save uploaded file
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"questions_{datetime.now().timestamp()}_{file.filename}")
    
    try:
        # Read and save file content
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Parse questions from PDF
        questions_data = PDFParser.parse_questions(file_path)
        
        if not questions_data:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No questions found in PDF. Please check the format."
            )
        
        # Create question set
        question_set = QuestionSet(
            title=title,
            pdf_filename=file.filename,
            uploaded_by=current_admin.id,
            is_active=True
        )
        db.add(question_set)
        db.commit()
        db.refresh(question_set)
        
        # Add questions to database
        for q_data in questions_data:
            question = Question(
                question_set_id=question_set.id,
                question_number=q_data["question_number"],
                question_text=q_data["question_text"]
            )
            db.add(question)
        
        db.commit()
        
        return {
            "message": f"Successfully uploaded {len(questions_data)} questions",
            "question_set_id": question_set.id,
            "total_questions": len(questions_data)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        # Clean up on error
        if os.path.exists(file_path):
            os.remove(file_path)
        # Log the full error for debugging
        import traceback
        print(f"Error processing PDF: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing PDF: {str(e)}"
        )



@router.post("/upload/answers/{question_set_id}", response_model=UploadResponse)
async def upload_answers(
    question_set_id: int,
    file: UploadFile = File(...),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Upload and parse answer sheet PDF"""
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    # Check if question set exists
    question_set = db.query(QuestionSet).filter(QuestionSet.id == question_set_id).first()
    if not question_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question set not found"
        )
    
    # Save uploaded file
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"answers_{datetime.now().timestamp()}_{file.filename}")
    
    try:
        # Read and save file content
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Parse answers from PDF
        answers_data = PDFParser.parse_answers(file_path)
        
        if not answers_data:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No answers found in PDF. Please check the format."
            )
        
        # Get questions for this set
        questions = db.query(Question).filter(Question.question_set_id == question_set_id).all()
        
        # Add answer keys to database
        added_count = 0
        for question in questions:
            if question.question_number in answers_data:
                # Check if answer key already exists
                existing_key = db.query(AnswerKey).filter(
                    AnswerKey.question_id == question.id
                ).first()
                
                if existing_key:
                    # Update existing answer key
                    existing_key.correct_answer = answers_data[question.question_number]
                    existing_key.pdf_filename = file.filename
                else:
                    # Create new answer key
                    answer_key = AnswerKey(
                        question_id=question.id,
                        correct_answer=answers_data[question.question_number],
                        pdf_filename=file.filename
                    )
                    db.add(answer_key)
                
                added_count += 1
        
        db.commit()
        
        return {
            "message": f"Successfully uploaded {added_count} answers",
            "question_set_id": question_set_id,
            "total_questions": added_count
        }
    
    except HTTPException:
        raise
    except Exception as e:
        # Clean up on error
        if os.path.exists(file_path):
            os.remove(file_path)
        # Log the full error for debugging
        import traceback
        print(f"Error processing PDF: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing PDF: {str(e)}"
        )


@router.get("/question-sets", response_model=List[QuestionSetResponse])
def get_question_sets(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all question sets"""
    question_sets = db.query(QuestionSet).all()
    
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

@router.get("/questions/{question_set_id}", response_model=List[QuestionWithAnswer])
def get_questions_with_answers(
    question_set_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all questions with their answers for a question set"""
    questions = db.query(Question).filter(Question.question_set_id == question_set_id).all()
    
    result = []
    for q in questions:
        answer_key = db.query(AnswerKey).filter(AnswerKey.question_id == q.id).first()
        result.append({
            "id": q.id,
            "question_number": q.question_number,
            "question_text": q.question_text,
            "correct_answer": answer_key.correct_answer if answer_key else None
        })
    
    return sorted(result, key=lambda x: x["question_number"])

@router.delete("/question-sets/{question_set_id}")
def delete_question_set(
    question_set_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete a question set and all associated data"""
    # Check if question set exists
    question_set = db.query(QuestionSet).filter(QuestionSet.id == question_set_id).first()
    if not question_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question set not found"
        )
    
    # Check if there are any active test sessions using this question set
    active_sessions = db.query(TestSession).filter(
        TestSession.question_set_id == question_set_id,
        TestSession.is_completed == False
    ).count()
    
    if active_sessions > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete question set with {active_sessions} active test session(s)"
        )
    
    try:
        # Delete the question set (cascade will handle questions and answer keys)
        db.delete(question_set)
        db.commit()
        
        return {
            "message": f"Question set '{question_set.title}' deleted successfully",
            "deleted_id": question_set_id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting question set: {str(e)}"
        )

@router.get("/results", response_model=List[CandidateResultSummary])
def get_all_results(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all candidate results"""
    sessions = db.query(TestSession).filter(TestSession.is_completed == True).all()
    
    results = []
    for session in sessions:
        candidate = db.query(User).filter(User.id == session.candidate_id).first()
        result = db.query(Result).filter(Result.session_id == session.id).first()
        
        if result:
            results.append({
                "candidate_username": candidate.username,
                "session_id": session.id,
                "submitted_at": session.submitted_at,
                "score_percentage": result.score_percentage,
                "passed": result.passed,
                "total_questions": result.total_questions,
                "correct_answers": result.correct_answers
            })
    
    return results

@router.get("/sessions")
def get_active_sessions(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all active test sessions"""
    sessions = db.query(TestSession).all()
    
    result = []
    for session in sessions:
        candidate = db.query(User).filter(User.id == session.candidate_id).first()
        question_set = db.query(QuestionSet).filter(QuestionSet.id == session.question_set_id).first()
        
        result.append({
            "session_id": session.id,
            "candidate_username": candidate.username,
            "question_set_title": question_set.title,
            "started_at": session.started_at,
            "is_completed": session.is_completed,
            "submitted_at": session.submitted_at
        })
    
    return result
