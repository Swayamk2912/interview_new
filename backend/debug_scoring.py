"""
Debug script to check answer keys vs candidate answers
"""
import sys
sys.path.append('c:/Users/sonuk/OneDrive/Desktop/Interview/interview_new/backend')

from database import SessionLocal
from models import TestSession, Question, AnswerKey, CandidateAnswer, Result

db = SessionLocal()

try:
    # Get the latest test session
    latest_session = db.query(TestSession).order_by(TestSession.id.desc()).first()
    
    if not latest_session:
        print("No sessions found")
        exit()
    
    print("=" * 80)
    print(f"Session ID: {latest_session.id}")
    print(f"Candidate: {latest_session.candidate_id}")
    print(f"Question Set: {latest_session.question_set_id}")
    print("=" * 80)
    
    # Get candidate answers
    candidate_answers = db.query(CandidateAnswer).filter(
        CandidateAnswer.session_id == latest_session.id
    ).all()
    
    print(f"\nTotal candidate answers: {len(candidate_answers)}\n")
    
    # For each answer, show what was submitted vs what was expected
    for cand_ans in candidate_answers[:10]:  # Show first 10
        question = db.query(Question).filter(Question.id == cand_ans.question_id).first()
        answer_key = db.query(AnswerKey).filter(AnswerKey.question_id == question.id).first()
        
        print(f"Q{question.question_number}:")
        print(f"  Candidate answered: '{cand_ans.answer_text}'")
        if answer_key:
            print(f"  Correct answer:     '{answer_key.correct_answer}'")
            print(f"  Match: {cand_ans.is_correct}")
            print(f"  Similarity: {cand_ans.similarity_score}")
        else:
            print(f"  No answer key found!")
        print()
    
    # Get result
    result = db.query(Result).filter(Result.session_id == latest_session.id).first()
    if result:
        print("=" * 80)
        print(f"RESULT: {result.correct_answers}/{result.total_questions} = {result.score_percentage}%")
        print("=" * 80)
    
finally:
    db.close()
