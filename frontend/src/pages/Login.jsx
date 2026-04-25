import React, { useState } from 'react';
import api from '../api/client';
import { useNavigate } from 'react-router-dom';
import './Login.css';

function Login() {
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
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const response = await api.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      localStorage.setItem('token', response.data.access_token);
      navigate('/dashboard');
    } catch (err) {
      setError('Invalid email/username or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container">
      <div className="auth-split-layout">
        <div className="auth-split-left">
          <div className="bg-circle-1"></div>
          <div className="bg-circle-2"></div>
          <div className="bg-circle-3"></div>

          <h1 className="font-display" style={{ fontSize: '48px', marginBottom: '16px', lineHeight: '1.1' }}>
            Land your dream job.<br />
            Beat every ATS filter.
          </h1>
          
          <ul className="auth-feature-list">
            <li className="auth-feature-item">
              <div className="auth-feature-icon">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
              </div>
              <div>
                <div className="auth-feature-text-title">AI-powered resume rewriting</div>
                <div className="auth-feature-text-sub">Intelligent keyword integration without stuffing</div>
              </div>
            </li>
            <li className="auth-feature-item">
              <div className="auth-feature-icon">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
              </div>
              <div>
                <div className="auth-feature-text-title">Weighted ATS score analysis</div>
                <div className="auth-feature-text-sub">Section-by-section breakdown of your match rate</div>
              </div>
            </li>
            <li className="auth-feature-item">
              <div className="auth-feature-icon">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
              </div>
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
              <h2 className="font-display">Welcome back</h2>
              <p>Sign in to continue optimizing</p>

              <form onSubmit={handleSubmit}>
                <div className="auth-input-group">
                  <label htmlFor="email-address">Email or Username</label>
                  <input
                    id="email-address"
                    name="email"
                    type="text"
                    className="auth-input-field"
                    autoComplete="username"
                    required
                    aria-invalid={!!error}
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>

                <div className="auth-input-group">
                  <label htmlFor="password">Password</label>
                  <input
                    id="password"
                    name="password"
                    type="password"
                    className="auth-input-field"
                    autoComplete="current-password"
                    required
                    aria-invalid={!!error}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '14px', color: 'var(--text-secondary)' }}>
                    <input type="checkbox" style={{ width: 'auto', height: 'auto' }} />
                    Remember me
                  </label>
                  <a href="#" className="link-text" style={{ fontSize: '14px', color: 'var(--accent)' }}>Forgot password?</a>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="auth-btn-primary"
                >
                  {loading ? (
                    <>
                      <div className="spin-ring"></div>
                      Signing in...
                    </>
                  ) : 'Sign in'}
                </button>
              </form>

              {error && (
                <div className="auth-error-badge" role="alert">
                  ✕ {error}
                </div>
              )}

              <div style={{ marginTop: '32px', textAlign: 'center' }} className="link-text">
                Don't have an account? <a href="/register">Sign up →</a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login;