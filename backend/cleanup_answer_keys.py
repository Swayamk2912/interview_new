"""
Utility script to clean up orphaned answer keys
(Answer keys that don't have corresponding questions)
"""
import sys
sys.path.append('c:/Users/sonuk/OneDrive/Desktop/Interview/interview_new/backend')

from database import SessionLocal
from models import Question, AnswerKey

db = SessionLocal()

try:
    print("=" * 80)
    print("CLEANING UP ORPHANED ANSWER KEYS")
    print("=" * 80)
    
    # Get all answer keys
    all_answer_keys = db.query(AnswerKey).all()
    print(f"\nTotal Answer Keys in Database: {len(all_answer_keys)}")
    
    # Find orphaned answer keys (where question doesn't exist)
    orphaned = []
    for answer_key in all_answer_keys:
        question = db.query(Question).filter(Question.id == answer_key.question_id).first()
        if not question:
            orphaned.append(answer_key)
    
    if orphaned:
        print(f"\n⚠️  Found {len(orphaned)} orphaned answer keys!")
        print("These answer keys will be deleted:")
        for ak in orphaned:
            print(f"  - Answer Key ID: {ak.id}, Question ID: {ak.question_id}")
        
        # Delete orphaned answer keys
        for ak in orphaned:
            db.delete(ak)
        
        db.commit()
        print(f"\n✅ Deleted {len(orphaned)} orphaned answer keys")
    else:
        print("\n✅ No orphaned answer keys found. Database is clean!")
    
    # Show final stats
    remaining = db.query(AnswerKey).count()
    questions_count = db.query(Question).count()
    print(f"\nFinal Stats:")
    print(f"  Total Questions: {questions_count}")
    print(f"  Total Answer Keys: {remaining}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    db.rollback()
finally:
    db.close()

print("\n" + "=" * 80)
print("CLEANUP COMPLETE")
print("=" * 80)
