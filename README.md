# Interview System

An offline interview management system with FastAPI backend and React frontend.

## Features

- **Admin Dashboard**: Upload question and answer PDFs, view results, monitor sessions
- **Candidate Interface**: Take tests, submit answers, view detailed results
- **Auto-Grading**: Automatic answer checking with multiple validation methods
- **Offline Operation**: Works completely offline using SQLite database

## Setup Instructions

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will run on http://localhost:8000

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run development server:
```bash
npm run dev
```

Frontend will run on http://localhost:5173

## Usage

### Admin Login
- Default credentials: `admin` / `admin123`
- Upload question and answer PDFs
- Monitor candidate sessions and results

### Candidate Registration
- Register with username and password
- Take the test
- View results with detailed feedback

## PDF Format

### Question PDF
Questions should be numbered:
```
1. What is Python?
2. Explain FastAPI.
3. What is React?
```

### Answer PDF
Answers should match question numbering:
```
1. Python is a high-level programming language.
2. FastAPI is a modern web framework for building APIs.
3. React is a JavaScript library for building user interfaces.
```

## Technologies

- **Backend**: FastAPI, SQLAlchemy, SQLite
- **Frontend**: React, Vite, React Router
- **PDF Processing**: PyMuPDF
- **Authentication**: JWT tokens
