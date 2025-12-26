import fitz  # PyMuPDF
import re
from typing import List, Dict, Tuple
import os

class PDFParser:
    """Service for parsing question and answer PDFs"""
    
    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> str:
        """Extract all text from a PDF file"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
    
    @staticmethod
    def parse_questions(pdf_path: str) -> List[Dict[str, any]]:
        """
        Parse questions from PDF.
        Supports multiple formats:
        - MCQ format: Q1, Q2 with options A, B, C, D
        - Simple numbered: "1. Question text", "2. Question text"
        """
        text = PDFParser.extract_text_from_pdf(pdf_path)
        questions = []
        
        # Try MCQ format first (Q1, Q2, etc.)
        # Pattern matches: Q1, Q2, Q10, etc. followed by question text and options
        mcq_pattern = r'Q(\d+)\s*\n?(.*?)(?=Q\d+|\Z)'
        matches = re.findall(mcq_pattern, text, re.DOTALL)
        
        if matches:
            for match in matches:
                question_number = int(match[0])
                question_block = match[1].strip()
                
                # Extract question text and options
                # Options are typically A. B. C. D. on separate lines
                lines = question_block.split('\n')
                question_text = []
                options = []
                
                current_option = None
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Check if line starts with option letter (A., B., C., D.)
                    option_match = re.match(r'^([A-D])\.\s*(.+)', line)
                    if option_match:
                        if current_option:
                            options.append(current_option)
                        current_option = f"{option_match.group(1)}. {option_match.group(2)}"
                    elif current_option:
                        # Continue previous option
                        current_option += " " + line
                    else:
                        # Part of question text
                        question_text.append(line)
                
                # Add last option
                if current_option:
                    options.append(current_option)
                
                # Combine question text
                full_question = ' '.join(question_text)
                if options:
                    full_question += '\n' + '\n'.join(options)
                
                if full_question:
                    questions.append({
                        "question_number": question_number,
                        "question_text": full_question.strip()
                    })
            
            return questions
        
        # Fallback to simple numbered format
        pattern = r'(?:^|\n)(?:Q(?:uestion)?\s*)?(\d+)[\.\:\)]\s*(.+?)(?=(?:\n(?:Q(?:uestion)?\s*)?\d+[\.\:\)]|\Z))'
        matches = re.findall(pattern, text, re.DOTALL | re.MULTILINE)
        
        for match in matches:
            question_number = int(match[0])
            question_text = match[1].strip()
            question_text = re.sub(r'\s+', ' ', question_text)
            
            questions.append({
                "question_number": question_number,
                "question_text": question_text
            })
        
        if not questions:
            questions = PDFParser._parse_questions_line_by_line(text)
        
        return questions
    
    @staticmethod
    def _parse_questions_line_by_line(text: str) -> List[Dict[str, any]]:
        """Fallback method to parse questions line by line"""
        lines = text.split('\n')
        questions = []
        current_question = None
        current_number = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts with a number
            match = re.match(r'^(?:Q(?:uestion)?\s*)?(\d+)[\.\:\)]\s*(.+)', line)
            if match:
                # Save previous question if exists
                if current_question and current_number:
                    questions.append({
                        "question_number": current_number,
                        "question_text": current_question.strip()
                    })
                
                # Start new question
                current_number = int(match.group(1))
                current_question = match.group(2)
            elif current_question is not None:
                # Continue previous question
                current_question += " " + line
        
        # Add the last question
        if current_question and current_number:
            questions.append({
                "question_number": current_number,
                "question_text": current_question.strip()
            })
        
        return questions
    
    @staticmethod
    def parse_answers(pdf_path: str) -> Dict[int, str]:
        """
        Parse answers from PDF.
        Supports formats:
        - Table format: Q1 on one line, then A. answer on next line
        - MCQ format: "1. A" or "Q1. A" (just the option letter)
        - Full text: "1. Answer text here"
        Returns dict mapping question_number to answer_text
        """
        text = PDFParser.extract_text_from_pdf(pdf_path)
        answers = {}
        
        # DEBUG: Print first 1000 characters of extracted text
        print("=" * 80)
        print("EXTRACTED TEXT FROM ANSWER PDF:")
        print(text[:1000])
        print("=" * 80)
        
        lines = text.split('\n')
        
        # STRATEGY 1: Try table format with Q# and answer on SAME line
        # Format: "Q1    ODQZM" or "Q1  \t  ODQZM" (separated by tabs/spaces)
        for line in lines:
            stripped = line.strip()
            if not stripped or 'Question' in stripped or 'SET' in stripped:
                continue  # Skip headers and empty lines
            
            # Match: Q## followed by whitespace/tab and then answer text
            match = re.match(r'^[Qq](\d+)[\s\t]+(.+)', stripped)
            if match:
                question_num = int(match.group(1))
                answer_text = match.group(2).strip()
                if answer_text:  # Only add if answer is not empty
                    answers[question_num] = answer_text
                    print(f"Found Q{question_num}: {answer_text}")
        
        if answers:
            print(f"Table format found {len(answers)} answers")
            print("=" * 80)
            return answers
        
        # STRATEGY 2: Try table format with Q1 on one line, answer on next (old format)
        # Pattern: Q1 on one line, followed by answer lines
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if line is exactly Q followed by number
            q_match = re.match(r'^Q(\d+)$', line)
            if q_match:
                question_num = int(q_match.group(1))
                print(f"Found Q{question_num}")
                
                # Look at the next line for SET A answer
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    print(f"  Next line: '{next_line}'")
                    
                    # Accept ANY non-empty answer (not just MCQ options A-D)
                    if next_line and not re.match(r'^Q\d+$', next_line):
                        answers[question_num] = next_line
                        print(f"  -> Answer: {next_line}")
            
            i += 1
        
        # DEBUG: Print final answers
        print(f"Total answers found: {len(answers)}")
        print(f"Answers: {answers}")
        print("=" * 80)
        
        # If table format found answers, return them
        if answers:
            return answers
        
        # Try MCQ format - just option letters
        # Pattern: "1. A" or "Q1. A" or "1) A"
        mcq_pattern = r'(?:^|\n)(?:Q(?:uestion)?\s*)?(\d+)[\.\:\)]\s*([A-D])\b'
        matches = re.findall(mcq_pattern, text, re.MULTILINE)
        
        if matches:
            for match in matches:
                answer_number = int(match[0])
                answer_letter = match[1]
                answers[answer_number] = answer_letter
            return answers
        
        # Fallback to full text answers
        pattern = r'(?:^|\n)(?:A(?:nswer)?\s*)?(\d+)[\.\:\)]\s*(.+?)(?=(?:\n(?:A(?:nswer)?\s*)?\d+[\.\:\)]|\Z))'
        matches = re.findall(pattern, text, re.DOTALL | re.MULTILINE)
        
        for match in matches:
            answer_number = int(match[0])
            answer_text = match[1].strip()
            answer_text = re.sub(r'\s+', ' ', answer_text)
            answers[answer_number] = answer_text
        
        if not answers:
            answers = PDFParser._parse_answers_line_by_line(text)
        
        return answers
    
    @staticmethod
    def _parse_answers_line_by_line(text: str) -> Dict[int, str]:
        """Fallback method to parse answers line by line"""
        lines = text.split('\n')
        answers = {}
        current_answer = None
        current_number = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts with a number
            match = re.match(r'^(?:A(?:nswer)?\s*)?(\d+)[\.\:\)]\s*(.+)', line)
            if match:
                # Save previous answer if exists
                if current_answer and current_number:
                    answers[current_number] = current_answer.strip()
                
                # Start new answer
                current_number = int(match.group(1))
                current_answer = match.group(2)
            elif current_answer is not None:
                # Continue previous answer
                current_answer += " " + line
        
        # Add the last answer
        if current_answer and current_number:
            answers[current_number] = current_answer.strip()
        
        return answers
