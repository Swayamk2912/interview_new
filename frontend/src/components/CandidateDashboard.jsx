import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import ThemeToggle from './ThemeToggle';
import './CandidateDashboard.css';

const CandidateDashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [view, setView] = useState('select'); // 'select', 'details-form', 'test', 'result'
  const [questionSets, setQuestionSets] = useState([]);
  const [selectedQuestionSet, setSelectedQuestionSet] = useState(null);
  const [session, setSession] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  // Candidate details state
  const [candidateDetails, setCandidateDetails] = useState({
    name: '',
    email: '',
    mobile: '',
    date: new Date().toISOString().split('T')[0], // Today's date
    batchTime: ''
  });

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

  const showDetailsForm = (questionSetId) => {
    setSelectedQuestionSet(questionSetId);
    setView('details-form');
  };

  const handleDetailsSubmit = async (e) => {
    e.preventDefault();

    // Validate all fields are filled
    if (!candidateDetails.name || !candidateDetails.email || !candidateDetails.mobile ||
      !candidateDetails.date || !candidateDetails.batchTime) {
      setError('Please fill in all required fields');
      return;
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(candidateDetails.email)) {
      setError('Please enter a valid email address');
      return;
    }

    // Mobile validation (10 digits)
    const mobileRegex = /^\d{10}$/;
    if (!mobileRegex.test(candidateDetails.mobile)) {
      setError('Please enter a valid 10-digit mobile number');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Start session with candidate details
      const sessionResponse = await api.post('/api/candidate/session/start', {
        question_set_id: selectedQuestionSet,
        candidate_name: candidateDetails.name,
        candidate_email: candidateDetails.email,
        candidate_mobile: candidateDetails.mobile,
        test_date: candidateDetails.date,
        batch_time: candidateDetails.batchTime
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
      <ThemeToggle />
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
                  <div key={qs.id} className={`card test-card ${qs.is_completed ? 'test-completed' : ''}`}>
                    <div className="test-card-header">
                      <h3 className="test-card-title">{qs.title}</h3>
                      {qs.is_completed && (
                        <div className="completed-badge">
                          ✅ Test Already Given
                        </div>
                      )}
                      <div className="test-stats">
                        <div className="stat-item">
                          <span className="stat-icon">📝</span>
                          <span>{qs.total_questions} Questions</span>
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => showDetailsForm(qs.id)}
                      className="btn btn-primary btn-block"
                      disabled={loading || qs.is_completed}
                    >
                      {qs.is_completed ? '🔒 Test Completed' : (loading ? 'Starting...' : 'Start Test')}
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Candidate Details Form */}
        {view === 'details-form' && (
          <div className="details-form-section">
            <div className="card details-form-card">
              <div className="card-header">
                <h2 className="card-title">📋 Candidate Information</h2>
                <p className="card-subtitle">Please fill in all details before starting the test</p>
              </div>

              <form onSubmit={handleDetailsSubmit}>
                <div className="grid grid-cols-2">
                  {/* Name */}
                  <div className="form-group">
                    <label className="form-label">Name *</label>
                    <input
                      type="text"
                      className="form-input"
                      value={candidateDetails.name}
                      onChange={(e) => setCandidateDetails({ ...candidateDetails, name: e.target.value })}
                      placeholder="Enter your full name"
                      required
                    />
                  </div>

                  {/* Email */}
                  <div className="form-group">
                    <label className="form-label">Email ID *</label>
                    <input
                      type="email"
                      className="form-input"
                      value={candidateDetails.email}
                      onChange={(e) => setCandidateDetails({ ...candidateDetails, email: e.target.value })}
                      placeholder="your.email@example.com"
                      required
                    />
                  </div>

                  {/* Mobile */}
                  <div className="form-group">
                    <label className="form-label">Mobile No. *</label>
                    <input
                      type="tel"
                      className="form-input"
                      value={candidateDetails.mobile}
                      onChange={(e) => setCandidateDetails({ ...candidateDetails, mobile: e.target.value })}
                      placeholder="10-digit mobile number"
                      pattern="[0-9]{10}"
                      maxLength="10"
                      required
                    />
                  </div>

                  {/* Date */}
                  <div className="form-group">
                    <label className="form-label">Date *</label>
                    <input
                      type="date"
                      className="form-input"
                      value={candidateDetails.date}
                      onChange={(e) => setCandidateDetails({ ...candidateDetails, date: e.target.value })}
                      required
                    />
                  </div>

                  {/* Batch Time */}
                  <div className="form-group" style={{ gridColumn: 'span 2' }}>
                    <label className="form-label">Batch Time *</label>
                    <input
                      type="text"
                      className="form-input"
                      value={candidateDetails.batchTime}
                      onChange={(e) => setCandidateDetails({ ...candidateDetails, batchTime: e.target.value })}
                      placeholder="e.g., Morning 9:00 AM - 12:00 PM"
                      required
                    />
                  </div>
                </div>

                <div className="form-actions">
                  <button
                    type="button"
                    onClick={() => setView('select')}
                    className="btn btn-outline"
                    disabled={loading}
                  >
                    ← Back
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={loading}
                  >
                    {loading ? 'Starting Test...' : 'Proceed to Test →'}
                  </button>
                </div>
              </form>
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

              {/* Congratulations/Encouragement Message */}
              {result.passed ? (
                <div className="congrats-message">
                  <div className="congrats-icon">🎉</div>
                  <h3 className="congrats-title">Congratulations! You Passed! 🎊</h3>
                  <p className="congrats-text">
                    Excellent work! You've successfully completed the test with a score of {result.score_percentage.toFixed(1)}%.
                    Keep up the great performance!
                  </p>
                </div>
              ) : (
                <div className="encourage-message">
                  <div className="encourage-icon">💪</div>
                  <h3 className="encourage-title">Keep Trying!</h3>
                  <p className="encourage-text">
                    Don't give up! Review the answers below and you'll do better next time.
                    You scored {result.score_percentage.toFixed(1)}% - you're getting there!
                  </p>
                </div>
              )}

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
