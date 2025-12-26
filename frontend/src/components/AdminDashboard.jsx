import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api/client';
import ThemeToggle from './ThemeToggle';
import './AdminDashboard.css';

const AdminDashboard = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('upload');
  const [questionSets, setQuestionSets] = useState([]);
  const [results, setResults] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  // Upload states
  const [questionFile, setQuestionFile] = useState(null);
  const [answerFile, setAnswerFile] = useState(null);
  const [questionSetTitle, setQuestionSetTitle] = useState('');
  const [selectedQuestionSet, setSelectedQuestionSet] = useState(null);

  // Preview states
  const [previewQuestions, setPreviewQuestions] = useState([]);

  useEffect(() => {
    if (activeTab === 'questions') {
      fetchQuestionSets();
    } else if (activeTab === 'results') {
      fetchResults();
    } else if (activeTab === 'sessions') {
      fetchSessions();
    }
  }, [activeTab]);

  const fetchQuestionSets = async () => {
    try {
      const response = await api.get('/api/admin/question-sets');
      setQuestionSets(response.data);
    } catch (error) {
      showMessage('error', 'Failed to fetch question sets');
    }
  };

  const fetchResults = async () => {
    try {
      const response = await api.get('/api/admin/results');
      setResults(response.data);
    } catch (error) {
      showMessage('error', 'Failed to fetch results');
    }
  };

  const fetchSessions = async () => {
    try {
      const response = await api.get('/api/admin/sessions');
      setSessions(response.data);
    } catch (error) {
      showMessage('error', 'Failed to fetch sessions');
    }
  };

  const showMessage = (type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  };

  const handleQuestionUpload = async (e) => {
    e.preventDefault();
    if (!questionFile || !questionSetTitle) {
      showMessage('error', 'Please provide both file and title');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('file', questionFile);
    formData.append('title', questionSetTitle);

    try {
      const response = await api.post('/api/admin/upload/questions', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      showMessage('success', response.data.message);
      setQuestionFile(null);
      setQuestionSetTitle('');
      setSelectedQuestionSet(response.data.question_set_id);
      fetchQuestionSets();
    } catch (error) {
      showMessage('error', error.response?.data?.detail || 'Upload failed');
    }
    setLoading(false);
  };

  const handleAnswerUpload = async (e) => {
    e.preventDefault();
    if (!answerFile || !selectedQuestionSet) {
      showMessage('error', 'Please select question set and answer file');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('file', answerFile);

    try {
      const response = await api.post(
        `/api/admin/upload/answers/${selectedQuestionSet}`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );

      showMessage('success', response.data.message);
      setAnswerFile(null);
    } catch (error) {
      showMessage('error', error.response?.data?.detail || 'Upload failed');
    }
    setLoading(false);
  };

  const viewQuestions = async (questionSetId) => {
    try {
      const response = await api.get(`/api/admin/questions/${questionSetId}`);
      setPreviewQuestions(response.data);
      setActiveTab('preview');
    } catch (error) {
      showMessage('error', 'Failed to load questions');
    }
  };

  const deleteQuestionSet = async (questionSetId, title) => {
    if (!window.confirm(`Are you sure you want to delete "${title}"? This action cannot be undone.`)) {
      return;
    }

    setLoading(true);
    try {
      const response = await api.delete(`/api/admin/question-sets/${questionSetId}`);
      showMessage('success', response.data.message);
      fetchQuestionSets();
    } catch (error) {
      showMessage('error', error.response?.data?.detail || 'Failed to delete question set');
    }
    setLoading(false);
  };

  return (
    <div className="admin-container">
      <ThemeToggle />
      {/* Header */}
      <header className="admin-header">
        <div className="header-content container">
          <h1 className="admin-title">
            <span className="gradient-text">Admin</span> Dashboard
          </h1>
          <div className="header-actions">
            <span className="user-badge">
              <span className="user-icon">👨‍💼</span>
              {user?.username}
            </span>
            <button onClick={logout} className="btn btn-outline btn-sm">
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="tabs-container container">
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveTab('upload')}
          >
            📤 Upload PDFs
          </button>
          <button
            className={`tab ${activeTab === 'questions' ? 'active' : ''}`}
            onClick={() => setActiveTab('questions')}
          >
            📝 Question Sets
          </button>
          <button
            className={`tab ${activeTab === 'results' ? 'active' : ''}`}
            onClick={() => setActiveTab('results')}
          >
            📊 Results
          </button>
          <button
            className={`tab ${activeTab === 'sessions' ? 'active' : ''}`}
            onClick={() => setActiveTab('sessions')}
          >
            👥 Sessions
          </button>
        </div>
      </div>

      {/* Main Content */}
      <main className="admin-main container">
        {message && (
          <div className={`alert alert-${message.type}`}>
            {message.text}
          </div>
        )}

        {/* Upload Tab */}
        {activeTab === 'upload' && (
          <div className="upload-section">
            <div className="grid grid-cols-2">
              {/* Question Upload */}
              <div className="card">
                <div className="card-header">
                  <h2 className="card-title">Upload Questions PDF</h2>
                  <p className="card-subtitle">Upload a PDF with numbered questions</p>
                </div>
                <form onSubmit={handleQuestionUpload}>
                  <div className="form-group">
                    <label className="form-label">Question Set Title</label>
                    <input
                      type="text"
                      className="form-input"
                      value={questionSetTitle}
                      onChange={(e) => setQuestionSetTitle(e.target.value)}
                      placeholder="e.g., Python Fundamentals Test"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Question PDF</label>
                    <input
                      type="file"
                      accept=".pdf"
                      onChange={(e) => setQuestionFile(e.target.files[0])}
                      className="file-input"
                    />
                    {questionFile && (
                      <div className="file-selected">{questionFile.name}</div>
                    )}
                  </div>
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={loading}
                  >
                    {loading ? 'Uploading...' : 'Upload Questions'}
                  </button>
                </form>
              </div>

              {/* Answer Upload */}
              <div className="card">
                <div className="card-header">
                  <h2 className="card-title">Upload Answers PDF</h2>
                  <p className="card-subtitle">Upload answer key for questions</p>
                </div>
                <form onSubmit={handleAnswerUpload}>
                  <div className="form-group">
                    <label className="form-label">Select Question Set</label>
                    <select
                      className="form-select"
                      value={selectedQuestionSet || ''}
                      onChange={(e) => setSelectedQuestionSet(e.target.value)}
                    >
                      <option value="">Choose a question set...</option>
                      {questionSets.map((qs) => (
                        <option key={qs.id} value={qs.id}>
                          {qs.title} ({qs.total_questions} questions)
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Answer PDF</label>
                    <input
                      type="file"
                      accept=".pdf"
                      onChange={(e) => setAnswerFile(e.target.files[0])}
                      className="file-input"
                    />
                    {answerFile && (
                      <div className="file-selected">{answerFile.name}</div>
                    )}
                  </div>
                  <button
                    type="submit"
                    className="btn btn-secondary"
                    disabled={loading}
                  >
                    {loading ? 'Uploading...' : 'Upload Answers'}
                  </button>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* Question Sets Tab */}
        {activeTab === 'questions' && (
          <div className="question-sets-section">
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Question Sets</h2>
                <p className="card-subtitle">Manage your question banks</p>
              </div>
              {questionSets.length === 0 ? (
                <p className="empty-state">No question sets uploaded yet</p>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Title</th>
                        <th>Questions</th>
                        <th>Uploaded</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {questionSets.map((qs) => (
                        <tr key={qs.id}>
                          <td><strong>{qs.title}</strong></td>
                          <td>{qs.total_questions}</td>
                          <td>{new Date(qs.uploaded_at).toLocaleDateString()}</td>
                          <td>
                            <span className={`badge badge-${qs.is_active ? 'success' : 'error'}`}>
                              {qs.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          <td>
                            <div className="flex gap-2">
                              <button
                                onClick={() => viewQuestions(qs.id)}
                                className="btn btn-sm btn-outline"
                              >
                                👁️ View
                              </button>
                              <button
                                onClick={() => deleteQuestionSet(qs.id, qs.title)}
                                className="btn btn-sm btn-error"
                                disabled={loading}
                              >
                                🗑️ Delete
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Preview Tab */}
        {activeTab === 'preview' && (
          <div className="preview-section">
            <div className="card">
              <div className="card-header flex-between">
                <div>
                  <h2 className="card-title">Question Preview</h2>
                  <p className="card-subtitle">{previewQuestions.length} questions</p>
                </div>
                <button
                  onClick={() => setActiveTab('questions')}
                  className="btn btn-outline btn-sm"
                >
                  ← Back
                </button>
              </div>
              <div className="questions-list">
                {previewQuestions.map((q) => (
                  <div key={q.id} className="question-item">
                    <div className="question-number">Q{q.question_number}</div>
                    <div className="question-content">
                      <p className="question-text">{q.question_text}</p>
                      {q.correct_answer && (
                        <div className="answer-preview">
                          <strong>Answer:</strong> {q.correct_answer}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Results Tab */}
        {activeTab === 'results' && (
          <div className="results-section">
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Candidate Results</h2>
                <p className="card-subtitle">View all test submissions</p>
              </div>
              {results.length === 0 ? (
                <p className="empty-state">No results available yet</p>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Candidate</th>
                        <th>Score</th>
                        <th>Correct</th>
                        <th>Total</th>
                        <th>Status</th>
                        <th>Submitted</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.map((result, idx) => (
                        <tr key={idx}>
                          <td><strong>{result.candidate_username}</strong></td>
                          <td>{result.score_percentage.toFixed(1)}%</td>
                          <td>{result.correct_answers}</td>
                          <td>{result.total_questions}</td>
                          <td>
                            <span className={`badge badge-${result.passed ? 'success' : 'error'}`}>
                              {result.passed ? 'Passed' : 'Failed'}
                            </span>
                          </td>
                          <td>{new Date(result.submitted_at).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Sessions Tab */}
        {activeTab === 'sessions' && (
          <div className="sessions-section">
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Test Sessions</h2>
                <p className="card-subtitle">Monitor active and completed sessions</p>
              </div>
              {sessions.length === 0 ? (
                <p className="empty-state">No sessions found</p>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Candidate</th>
                        <th>Question Set</th>
                        <th>Started</th>
                        <th>Status</th>
                        <th>Submitted</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sessions.map((session, idx) => (
                        <tr key={idx}>
                          <td><strong>{session.candidate_username}</strong></td>
                          <td>{session.question_set_title}</td>
                          <td>{new Date(session.started_at).toLocaleString()}</td>
                          <td>
                            <span className={`badge badge-${session.is_completed ? 'success' : 'warning'}`}>
                              {session.is_completed ? 'Completed' : 'In Progress'}
                            </span>
                          </td>
                          <td>
                            {session.submitted_at
                              ? new Date(session.submitted_at).toLocaleString()
                              : '-'
                            }
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default AdminDashboard;
