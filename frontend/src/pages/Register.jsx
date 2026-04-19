import React, { useState } from 'react';
import api from '../api/client';
import { useNavigate } from 'react-router-dom';
import './Register.css';

function Register() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const response = await api.post('/auth/register', {
        username,
        email,
        password
      });
      
      localStorage.setItem('token', response.data.access_token);
      navigate('/dashboard');
    } catch (err) {
      setError('Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container">
      <div className="auth-split-layout">
        <div className="auth-split-left">
          <div className="auth-circle-1"></div>
          <div className="auth-circle-2"></div>
          <div className="auth-circle-3"></div>

          <h1 className="font-display" style={{ fontSize: '48px', marginBottom: '16px', lineHeight: '1.1' }}>
            Land your dream job.<br />
            Beat every ATS filter.
          </h1>
          
          <ul className="auth-feature-list">
            <li className="auth-feature-item">
              <div className="auth-feature-icon">✦</div>
              <div>
                <div className="auth-feature-text-title">AI-powered resume rewriting</div>
                <div className="auth-feature-text-sub">Intelligent keyword integration without stuffing</div>
              </div>
            </li>
            <li className="auth-feature-item">
              <div className="auth-feature-icon">✦</div>
              <div>
                <div className="auth-feature-text-title">Weighted ATS score analysis</div>
                <div className="auth-feature-text-sub">Section-by-section breakdown of your match rate</div>
              </div>
            </li>
            <li className="auth-feature-item">
              <div className="auth-feature-icon">✦</div>
              <div>
                <div className="auth-feature-text-title">Professional LaTeX PDF export</div>
                <div className="auth-feature-text-sub">Clean, machine-readable formatting every time</div>
              </div>
            </li>
          </ul>
        </div>

        <div className="auth-split-right">
          <div className="auth-card-wrapper">
            <div className="auth-card-inner">
              <h2 className="font-display">Create your account</h2>
              <p>Start building better resumes today</p>

              <form onSubmit={handleSubmit}>
                <div className="auth-input-group">
                  <label htmlFor="username">Username</label>
                  <input
                    id="username"
                    name="username"
                    type="text"
                    className="auth-input-field"
                    autoComplete="username"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                  />
                </div>

                <div className="auth-input-group">
                  <label htmlFor="email-address">Email address</label>
                  <input
                    id="email-address"
                    name="email"
                    type="email"
                    className="auth-input-field"
                    autoComplete="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>

                <div className="auth-input-group" style={{ marginBottom: '32px' }}>
                  <label htmlFor="password">Password</label>
                  <input
                    id="password"
                    name="password"
                    type="password"
                    className="auth-input-field"
                    autoComplete="new-password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="auth-btn-primary"
                >
                  {loading ? (
                    <>
                      <div className="spin-ring"></div>
                      Creating account...
                    </>
                  ) : 'Create account'}
                </button>
              </form>

              {error && (
                <div className="auth-error-badge">
                  ✕ {error}
                </div>
              )}

              <div style={{ marginTop: '32px', textAlign: 'center' }} className="link-text">
                Already have an account? <a href="/login">Sign in →</a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Register;