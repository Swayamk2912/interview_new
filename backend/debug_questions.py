import sys
sys.path.append('c:/Users/sonuk/OneDrive/Desktop/Interview/interview_new/backend')

from database import SessionLocal
from models import QuestionSet, Question, AnswerKey

# Create database session
db = SessionLocal()

try:
    # Get all question sets
    question_sets = db.query(QuestionSet).all()
    
    print("=" * 80)
    print("QUESTION SET ANALYSIS")
    print("=" * 80)
    
    for qs in question_sets:
        print(f"\nQuestion Set ID: {qs.id}")
        print(f"Title: {qs.title}")
        print(f"Active: {qs.is_active}")
        
        # Get all questions for this set
        questions = db.query(Question).filter(Question.question_set_id == qs.id).all()
        print(f"\nTotal Questions: {len(questions)}")
        
        # Check for duplicate question numbers
        question_numbers = [q.question_number for q in questions]
        duplicates = [num for num in set(question_numbers) if question_numbers.count(num) > 1]
        
        if duplicates:
            print(f"⚠️  DUPLICATE QUESTION NUMBERS FOUND: {duplicates}")
        
        # Count answer keys
        answer_count = 0
        questions_without_answers = []
        
        for q in questions:
            answer_key = db.query(AnswerKey).filter(AnswerKey.question_id == q.id).first()
            if answer_key:
                answer_count += 1
            else:
                questions_without_answers.append(q.question_number)
        
        print(f"Questions with Answer Keys: {answer_count}")
        
        if questions_without_answers:
            print(f"⚠️  Questions WITHOUT Answer Keys: {questions_without_answers}")
        
        # Show question numbers
        print(f"\nQuestion Numbers: {sorted(question_numbers)}")
        
        print("-" * 80)
    
finally:
    db.close()

print("\n✅ Analysis complete!")
