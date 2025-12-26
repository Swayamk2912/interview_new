from typing import List, Dict, Tuple
import Levenshtein
import re

class GradingService:
    """Service for grading candidate answers"""
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """Calculate similarity between two texts using Levenshtein distance"""
        # Normalize texts
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        
        if not text1 or not text2:
            return 0.0
        
        # Calculate Levenshtein ratio (0-1, where 1 is identical)
        ratio = Levenshtein.ratio(text1, text2)
        return ratio
    
    @staticmethod
    def exact_match(candidate_answer: str, correct_answer: str, case_sensitive: bool = False) -> bool:
        """Check if answers match exactly"""
        if not case_sensitive:
            candidate_answer = candidate_answer.lower().strip()
            correct_answer = correct_answer.lower().strip()
        else:
            candidate_answer = candidate_answer.strip()
            correct_answer = correct_answer.strip()
        
        return candidate_answer == correct_answer
    
    @staticmethod
    def fuzzy_match(candidate_answer: str, correct_answer: str, threshold: float = 0.8) -> Tuple[bool, float]:
        """
        Check if answers match using fuzzy matching
        Returns (is_match, similarity_score)
        """
        similarity = GradingService.calculate_similarity(candidate_answer, correct_answer)
        is_match = similarity >= threshold
        return is_match, similarity
    
    @staticmethod
    def keyword_match(candidate_answer: str, correct_answer: str, threshold: float = 0.6) -> Tuple[bool, float]:
        """
        Check if candidate answer contains key terms from correct answer
        Returns (is_match, match_percentage)
        """
        # Extract words from correct answer (ignore common words)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'is', 'are', 'was', 'were', 'be', 'been'}
        
        correct_words = set(re.findall(r'\w+', correct_answer.lower()))
        correct_words = correct_words - stop_words
        
        if not correct_words:
            return False, 0.0
        
        candidate_words = set(re.findall(r'\w+', candidate_answer.lower()))
        
        # Calculate how many keywords are present
        matched_keywords = correct_words.intersection(candidate_words)
        match_percentage = len(matched_keywords) / len(correct_words)
        
        is_match = match_percentage >= threshold
        return is_match, match_percentage
    
    @staticmethod
    def grade_answer(
        candidate_answer: str, 
        correct_answer: str, 
        method: str = "fuzzy",
        threshold: float = 0.75
    ) -> Dict[str, any]:
        """
        Grade a single answer using specified method
        
        Automatically detects MCQ format (single letter A-D) and uses exact matching.
        
        Methods:
        - exact: Exact match (case-insensitive)
        - fuzzy: Similarity-based matching using Levenshtein distance
        - keyword: Keyword-based matching
        
        Returns dict with is_correct and similarity_score
        """
        # Auto-detect MCQ format (single letter answer)
        correct_stripped = correct_answer.strip().upper()
        candidate_stripped = candidate_answer.strip().upper()
        
        # Check if both are single letters (MCQ format)
        if len(correct_stripped) == 1 and correct_stripped in 'ABCD':
            # MCQ answer - use exact matching
            is_correct = candidate_stripped == correct_stripped
            return {
                "is_correct": is_correct,
                "similarity_score": 1.0 if is_correct else 0.0
            }
        
        # Regular text answer - use specified method
        if method == "exact":
            is_correct = GradingService.exact_match(candidate_answer, correct_answer)
            return {
                "is_correct": is_correct,
                "similarity_score": 1.0 if is_correct else 0.0
            }
        
        elif method == "fuzzy":
            is_correct, similarity = GradingService.fuzzy_match(candidate_answer, correct_answer, threshold)
            return {
                "is_correct": is_correct,
                "similarity_score": similarity
            }
        
        elif method == "keyword":
            is_correct, match_percentage = GradingService.keyword_match(candidate_answer, correct_answer, threshold)
            return {
                "is_correct": is_correct,
                "similarity_score": match_percentage
            }
        
        else:
            # Default to fuzzy matching
            is_correct, similarity = GradingService.fuzzy_match(candidate_answer, correct_answer, threshold)
            return {
                "is_correct": is_correct,
                "similarity_score": similarity
            }
    
    @staticmethod
    def grade_test(
        candidate_answers: List[Dict],
        correct_answers: Dict[int, str],
        method: str = "fuzzy",
        threshold: float = 0.75,
        passing_percentage: float = 60.0
    ) -> Dict[str, any]:
        """
        Grade an entire test
        
        candidate_answers: List of {question_number, answer_text}
        correct_answers: Dict mapping question_number to correct answer
        
        Returns detailed grading results
        """
        total_questions = len(correct_answers)
        correct_count = 0
        graded_answers = []
        
        for answer_data in candidate_answers:
            question_num = answer_data["question_number"]
            candidate_ans = answer_data["answer_text"]
            
            if question_num not in correct_answers:
                continue
            
            correct_ans = correct_answers[question_num]
            
            result = GradingService.grade_answer(candidate_ans, correct_ans, method, threshold)
            
            if result["is_correct"]:
                correct_count += 1
            
            graded_answers.append({
                "question_number": question_num,
                "candidate_answer": candidate_ans,
                "correct_answer": correct_ans,
                "is_correct": result["is_correct"],
                "similarity_score": result["similarity_score"]
            })
        
        score_percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
        passed = score_percentage >= passing_percentage
        
        return {
            "total_questions": total_questions,
            "correct_answers": correct_count,
            "score_percentage": score_percentage,
            "passed": passed,
            "graded_answers": graded_answers
        }
