"""
Script to fix existing answer keys by extracting option letters
Converts "A. 20" to "A", "B. text" to "B", etc.
"""
import sys
sys.path.append('c:/Users/sonuk/OneDrive/Desktop/Interview/interview_new/backend')

from database import SessionLocal
from models import AnswerKey
import re

db = SessionLocal()

try:
    # Get all answer keys
    answer_keys = db.query(AnswerKey).all()
    
    print(f"Found {len(answer_keys)} answer keys to check")
    
    updated_count = 0
    
    for ak in answer_keys:
        original = ak.correct_answer
        
        # Check if answer starts with option letter (A., B., C., D.)
        option_match = re.match(r'^([A-D])\.?\s*', original)
        
        if option_match:
            # Extract just the letter
            new_answer = option_match.group(1)
            
            if new_answer != original:
                print(f"Q{ak.question_id}: '{original}' -> '{new_answer}'")
                ak.correct_answer = new_answer
                updated_count += 1
    
    db.commit()
    
    print(f"\n✅ Updated {updated_count} answer keys")
    print(f"✅ Kept {len(answer_keys) - updated_count} answer keys unchanged")
    
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
