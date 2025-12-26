import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import './Login.css';

const Login = () => {
  const [mode, setMode] = useState('candidate'); // 'candidate' or 'admin'
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login, register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    if (!username || !password) {
      setError('Please fill in all fields');
      setLoading(false);
      return;
    }

    let result;
    if (isRegister && mode === 'candidate') {
      result = await register(username, password);
    } else {
      result = await login(username, password, mode);
    }

    if (result.success) {
      if (mode === 'admin') {
        navigate('/admin');
      } else {
        navigate('/candidate');
      }
    } else {
      setError(result.error);
    }

    setLoading(false);
  };

  return (
    <div className="login-container">
      <div className="login-hero">
        <div className="hero-content">
          <h1 className="hero-title">
            <span className="gradient-text">Interview</span> System
          </h1>
          <p className="hero-subtitle">
            Advanced Offline Assessment Platform
          </p>
          <div className="hero-features">
            <div className="feature-item">
              <span className="feature-icon">📄</span>
              <span>PDF Processing</span>
            </div>
            <div className="feature-item">
              <span className="feature-icon">🤖</span>
              <span>Auto Grading</span>
            </div>
            <div className="feature-item">
              <span className="feature-icon">📊</span>
              <span>Real-time Results</span>
            </div>
          </div>
        </div>
      </div>

      <div className="login-form-container">
        <div className="card login-card">
          <div className="card-header">
            <h2 className="card-title">Welcome Back</h2>
            <p className="card-subtitle">
              {isRegister ? 'Create your account' : 'Sign in to continue'}
            </p>
          </div>

          {/* Role Selector */}
          <div className="role-selector">
            <button
              type="button"
              className={`role-btn ${mode === 'candidate' ? 'active' : ''}`}
              onClick={() => setMode('candidate')}
            >
              <span className="role-icon">👤</span>
              Candidate
            </button>
            <button
              type="button"
              className={`role-btn ${mode === 'admin' ? 'active' : ''}`}
              onClick={() => {
                setMode('admin');
                setIsRegister(false);
              }}
            >
              <span className="role-icon">👨‍💼</span>
              Admin
            </button>
          </div>

          {error && <div className="alert alert-error">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Username</label>
              <input
                type="text"
                className="form-input"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                autoComplete="username"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <input
                type="password"
                className="form-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                autoComplete="current-password"
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-block"
              disabled={loading}
            >
              {loading ? (
                <span className="flex-center gap-2">
                  <div className="spinner-small"></div>
                  Processing...
                </span>
              ) : isRegister ? (
                'Create Account'
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {mode === 'candidate' && (
            <div className="form-footer">
              <p>
                {isRegister ? 'Already have an account?' : "Don't have an account?"}
                <button
                  type="button"
                  className="link-btn"
                  onClick={() => {
                    setIsRegister(!isRegister);
                    setError('');
                  }}
                >
                  {isRegister ? 'Sign In' : 'Register'}
                </button>
              </p>
            </div>
          )}

          {mode === 'admin' && (
            <div className="admin-info">
              <small>Default credentials: admin / admin123</small>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Login;
