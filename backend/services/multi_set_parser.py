"""
Enhanced PDF Parser for Multi-Set Answer Sheets
Handles answer PDFs with multiple sets in table format (SET A, SET B, SET C)
"""
import fitz  # PyMuPDF
import re
from typing import Dict, List

class MultiSetAnswerParser:
    """Parser for answer PDFs containing multiple sets in columns"""
    
    @staticmethod
    def parse_multi_set_answers(pdf_path: str) -> Dict[str, Dict[int, str]]:
        """
        Parse a PDF with multiple answer sets in table format
        
        Expected format:
        Question Number | SET A | SET B | SET C
        Q1             | A. 20 | B. ODQZM | C. HAK
        Q2             | A. 250 m | A. 27 | A. QSHSBN
        ...
        
        Returns:
        {
            'SET A': {1: 'A. 20', 2: 'A. 250 m', ...},
            'SET B': {1: 'B. ODQZM', 2: 'A. 27', ...},
            'SET C': {1: 'C. HAK', 2: 'A. QSHSBN', ...}
        }
        """
        doc = fitz.open(pdf_path)
        full_text = ""
        
        # Extract all text
        for page in doc:
            full_text += page.get_text()
        
        doc.close()
        
        # Initialize result structure
        results = {
            'SET A': {},
            'SET B': {},
            'SET C': {}
        }
        
        # Split into lines
        lines = full_text.split('\n')
        
        # Find and verify header
        header_found = False
        for line in lines:
            upper_line = line.upper()
            if ('SET A' in upper_line or 'SETA' in upper_line) and \
               ('SET B' in upper_line or 'SETB' in upper_line) and \
               ('SET C' in upper_line or 'SETC' in upper_line):
                header_found = True
                print(f"Found header: {line}")
                break
        
        if not header_found:
            raise ValueError("Could not find SET A, SET B, SET C headers in PDF")
        
        # Parse answer rows
        for line in lines:
            # Skip empty lines and headers
            stripped = line.strip()
            if not stripped or 'SET' in stripped.upper() or 'Question' in stripped:
                continue
            
            # Try to match question number (Q1, Q01, 01, etc.)
            q_match = re.match(r'^[Qq]?[0]*(\d+)', stripped)
            if not q_match:
                continue
            
            question_num = int(q_match.group(1))
            
            # Split the line by various delimiters
            # Try tabs first, then pipes, then multiple spaces
            parts = None
            if '\t' in line:
                parts = [p.strip() for p in line.split('\t') if p.strip()]
            elif '|' in line:
                parts = [p.strip() for p in line.split('|') if p.strip()]
            else:
                # Split by 2+ spaces
                parts = [p.strip() for p in re.split(r'\s{2,}', line) if p.strip()]
            
            if not parts or len(parts) < 4:
                continue
            
            # First part is question number, next 3 are answers for A, B, C
            # parts[0] = Q#
            # parts[1] = SET A answer
            # parts[2] = SET B answer  
            # parts[3] = SET C answer
            
            try:
                set_a_answer = parts[1].strip()
                set_b_answer = parts[2].strip()
                set_c_answer = parts[3].strip()
                
                # Only add if we have non-empty answers
                if set_a_answer:
                    results['SET A'][question_num] = set_a_answer
                if set_b_answer:
                    results['SET B'][question_num] = set_b_answer
                if set_c_answer:
                    results['SET C'][question_num] = set_c_answer
                    
            except IndexError:
                # Not enough columns, skip this line
                continue
        
        # Validate we got answers
        for set_name, answers in results.items():
            if not answers:
                raise ValueError(f"No answers found for {set_name}. Please check PDF format.")
        
        print(f"Parsed answers: SET A={len(results['SET A'])}, SET B={len(results['SET B'])}, SET C={len(results['SET C'])}")
        
        return results
    
    @staticmethod
    def extract_set(multi_set_data: Dict[str, Dict[int, str]], set_name: str) -> Dict[int, str]:
        """
        Extract answers for a specific set
        
        Args:
            multi_set_data: Output from parse_multi_set_answers
            set_name: 'SET A', 'SET B', or 'SET C'
        
        Returns:
            Dict mapping question_number to answer text
        """
        if set_name not in multi_set_data:
            available = list(multi_set_data.keys())
            raise ValueError(f"Set '{set_name}' not found. Available: {available}")
        
        return multi_set_data[set_name]
