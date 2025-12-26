import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import './CandidateDashboard.css';

const CandidateDashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  
  const [view, setView] = useState('select'); // 'select', 'test', 'result'
  const [questionSets, setQuestionSets] = useState([]);
  const [selectedQuestionSet, setSelectedQuestionSet] = useState(null);
  const [session, setSession] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  useEffect(() => {
    if (view === 'select') {
      fetchQuestionSets();
    }
  }, [view]);

  const fetchQuestionSets = async () => {
    try {
      const response = await api.get('/api/candidate/question-sets');
      setQuestionSets(response.data);
    } catch (err) {
      setError('Failed to load question sets');
    }
  };

  const startTest = async (questionSetId) => {
    setLoading(true);
    setError(null);
    
    try {
      // Start session
      const sessionResponse = await api.post('/api/candidate/session/start', {
        question_set_id: questionSetId
      });
      
      const sessionData = sessionResponse.data;
      setSession(sessionData);
      
      // Get questions
      const questionsResponse = await api.get(`/api/candidate/test/${sessionData.id}`);
      setQuestions(questionsResponse.data);
      
      // Initialize answers
      const initialAnswers = {};
      questionsResponse.data.forEach(q => {
        initialAnswers[q.id] = '';
      });
      setAnswers(initialAnswers);
      
      setView('test');
      setCurrentQuestionIndex(0);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start test');
    }
    
    setLoading(false);
  };

  const handleAnswerChange = (questionId, value) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: value
    }));
  };

  const submitTest = async () => {
    if (!confirm('Are you sure you want to submit? You cannot change answers after submission.')) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Map answers to the correct format
      const answersList = questions.map(q => ({
        question_id: q.id,
        answer_text: answers[q.id] || '' // Send empty string if not answered
      }));

      console.log('Submitting answers:', answersList);

      const response = await api.post('/api/candidate/submit', {
        session_id: session.id,
        answers: answersList
      });

      console.log('Response:', response.data);
      setResult(response.data);
      setView('result');
    } catch (err) {
      console.error('Submit error:', err);
      setError(err.response?.data?.detail || 'Failed to submit test');
    }

    setLoading(false);
  };

  const currentQuestion = questions[currentQuestionIndex];
  const progress = ((currentQuestionIndex + 1) / questions.length) * 100;

  return (
    <div className="candidate-container">
      {/* Header */}
      <header className="candidate-header">
        <div className="header-content container">
          <h1 className="candidate-title">
            <span className="gradient-text">Candidate</span> Portal
          </h1>
          <div className="header-actions">
            <span className="user-badge">
              <span className="user-icon">👤</span>
              {user?.username}
            </span>
            <button onClick={logout} className="btn btn-outline btn-sm">
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="candidate-main container">
        {error && (
          <div className="alert alert-error">{error}</div>
        )}

        {/* Select Question Set View */}
        {view === 'select' && (
          <div className="select-test-section">
            <div className="card welcome-card">
              <div className="welcome-header">
                <h2 className="welcome-title">Welcome, {user?.username}! 👋</h2>
                <p className="welcome-subtitle">
                  Select a test to begin your assessment
                </p>
              </div>
            </div>

            <div className="question-sets-grid">
              {questionSets.length === 0 ? (
                <div className="card">
                  <p className="empty-state">No tests available at the moment</p>
                </div>
              ) : (
                questionSets.map((qs) => (
                  <div key={qs.id} className="card test-card">
                    <div className="test-card-header">
                      <h3 className="test-card-title">{qs.title}</h3>
                      <div className="test-stats">
                        <div className="stat-item">
                          <span className="stat-icon">📝</span>
                          <span>{qs.total_questions} Questions</span>
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => startTest(qs.id)}
                      className="btn btn-primary btn-block"
                      disabled={loading}
                    >
                      {loading ? 'Starting...' : 'Start Test'}
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Test Taking View */}
        {view === 'test' && currentQuestion && (
          <div className="test-section">
            {/* Progress Bar */}
            <div className="progress-container">
              <div className="progress-info">
                <span>Question {currentQuestionIndex + 1} of {questions.length}</span>
                <span>{Math.round(progress)}% Complete</span>
              </div>
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>

            {/* Question Card */}
            <div className="card question-card">
              <div className="question-header">
                <span className="question-badge">Q{currentQuestionIndex + 1}</span>
                <h2 className="question-title">
                  {(() => {
                    // Parse question to extract main question text (before options)
                    const questionText = currentQuestion.question_text;
                    const lines = questionText.split('\n');
                    const mainQuestion = [];
                    
                    for (let line of lines) {
                      // Stop at first option line (A., B., C., D.)
                      if (/^[A-D]\./.test(line.trim())) {
                        break;
                      }
                      mainQuestion.push(line);
                    }
                    
                    return mainQuestion.join(' ').trim();
                  })()}
                </h2>
              </div>

              <div className="answer-section">
                {(() => {
                  // Extract options from question text
                  const questionText = currentQuestion.question_text;
                  const lines = questionText.split('\n');
                  const options = [];
                  
                  for (let line of lines) {
                    const trimmed = line.trim();
                    // Match lines starting with A., B., C., D.
                    const match = trimmed.match(/^([A-D])\.\s*(.+)/);
                    if (match) {
                      options.push({
                        letter: match[1],
                        text: match[2]
                      });
                    }
                  }
                  
                  // If we found options, show radio buttons
                  if (options.length > 0) {
                    return (
                      <div className="mcq-options">
                        <label className="form-label">Select Your Answer:</label>
                        {options.map((option) => (
                          <div
                            key={option.letter}
                            className={`mcq-option ${answers[currentQuestion.id] === option.letter ? 'selected' : ''}`}
                            onClick={() => handleAnswerChange(currentQuestion.id, option.letter)}
                          >
                            <input
                              type="radio"
                              name={`question-${currentQuestion.id}`}
                              value={option.letter}
                              checked={answers[currentQuestion.id] === option.letter}
                              onChange={() => handleAnswerChange(currentQuestion.id, option.letter)}
                            />
                            <div className="option-content">
                              <span className="option-letter">{option.letter}</span>
                              <span className="option-text">{option.text}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    );
                  } else {
                    // Fallback to textarea for non-MCQ questions
                    return (
                      <>
                        <label className="form-label">Your Answer</label>
                        <textarea
                          className="form-textarea"
                          value={answers[currentQuestion.id] || ''}
                          onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
                          placeholder="Type your answer here..."
                          rows="6"
                        />
                      </>
                    );
                  }
                })()}
              </div>

              {/* Navigation */}
              <div className="question-navigation">
                <button
                  onClick={() => setCurrentQuestionIndex(prev => Math.max(0, prev - 1))}
                  disabled={currentQuestionIndex === 0}
                  className="btn btn-outline"
                >
                  ← Previous
                </button>
                
                <div className="question-dots">
                  {questions.map((q, idx) => (
                    <button
                      key={q.id}
                      onClick={() => setCurrentQuestionIndex(idx)}
                      className={`question-dot ${idx === currentQuestionIndex ? 'active' : ''} ${answers[q.id] ? 'answered' : ''}`}
                      title={`Question ${idx + 1}`}
                    >
                      {idx + 1}
                    </button>
                  ))}
                </div>

                {currentQuestionIndex === questions.length - 1 ? (
                  <button
                    onClick={submitTest}
                    className="btn btn-success"
                    disabled={loading}
                  >
                    {loading ? 'Submitting...' : 'Submit Test ✓'}
                  </button>
                ) : (
                  <button
                    onClick={() => setCurrentQuestionIndex(prev => Math.min(questions.length - 1, prev + 1))}
                    className="btn btn-primary"
                  >
                    Next →
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Results View */}
        {view === 'result' && result && (
          <div className="results-section">
            {/* Score Card */}
            <div className="card score-card">
              <div className="score-header">
                <h2 className="card-title">Test Results</h2>
                <div className={`score-badge ${result.passed ? 'passed' : 'failed'}`}>
                  {result.passed ? '✓ Passed' : '✗ Failed'}
                </div>
              </div>

              <div className="score-display">
                <div className="score-circle">
                  <svg viewBox="0 0 100 100">
                    <circle className="score-circle-bg" cx="50" cy="50" r="45" />
                    <circle 
                      className="score-circle-fill" 
                      cx="50" 
                      cy="50" 
                      r="45"
                      style={{
                        strokeDasharray: `${result.score_percentage * 2.827}, 282.7`
                      }}
                    />
                  </svg>
                  <div className="score-text">
                    <span className="score-percentage">{result.score_percentage.toFixed(1)}%</span>
                    <span className="score-label">Score</span>
                  </div>
                </div>

                <div className="score-stats">
                  <div className="stat-box">
                    <span className="stat-value">{result.correct_answers}</span>
                    <span className="stat-label">Correct</span>
                  </div>
                  <div className="stat-box">
                    <span className="stat-value">{result.total_questions - result.correct_answers}</span>
                    <span className="stat-label">Incorrect</span>
                  </div>
                  <div className="stat-box">
                    <span className="stat-value">{result.total_questions}</span>
                    <span className="stat-label">Total</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Detailed Answers */}
            <div className="card answers-card">
              <div className="card-header">
                <h3 className="card-title">Detailed Breakdown</h3>
              </div>

              <div className="answers-list">
                {result.answer_details.map((detail, idx) => (
                  <div key={idx} className={`answer-item ${detail.is_correct ? 'correct' : 'incorrect'}`}>
                    <div className="answer-item-header">
                      <span className="question-num">Q{detail.question_number}</span>
                      <span className={`result-badge ${detail.is_correct ? 'correct' : 'incorrect'}`}>
                        {detail.is_correct ? '✓ Correct' : '✗ Incorrect'}
                      </span>
                      {detail.similarity_score !== null && (
                        <span className="similarity-badge">
                          {(detail.similarity_score * 100).toFixed(0)}% Match
                        </span>
                      )}
                    </div>

                    <p className="answer-question">{detail.question_text}</p>

                    <div className="answer-comparison">
                      <div className="your-answer">
                        <strong>Your Answer:</strong>
                        <p>{detail.candidate_answer || '(No answer provided)'}</p>
                      </div>
                      <div className="correct-answer">
                        <strong>Correct Answer:</strong>
                        <p>{detail.correct_answer}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={() => {
                setView('select');
                setSession(null);
                setQuestions([]);
                setAnswers({});
                setResult(null);
              }}
              className="btn btn-primary btn-block mt-3"
            >
              Take Another Test
            </button>
          </div>
        )}
      </main>
    </div>
  );
};

export default CandidateDashboard;
