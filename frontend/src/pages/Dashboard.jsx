import React, { useState } from 'react';
import api from '../api/client';
import Navbar from '../components/Navbar';
import ResumeInput from '../components/ResumeInput';
import ATSScoreCard from '../components/ATSScoreCard';
import RewrittenPreview from '../components/RewrittenPreview';
import HistoryCard from '../components/HistoryCard';
import './Dashboard.css';

function Dashboard() {
  const [resumeText, setResumeText] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [provider, setProvider] = useState(() => {
    return localStorage.getItem('llm_provider') || 'gemini';
  });

  const handleProviderChange = (e) => {
    const val = e.target.value;
    setProvider(val);
    localStorage.setItem('llm_provider', val);
  };

  const [personalKey, setPersonalKey] = useState(() => {
    return localStorage.getItem('personal_gemini_key') || '';
  });
  const [showKey, setShowKey] = useState(false);

  const handlePersonalKeyChange = (e) => {
    const val = e.target.value.trim();
    setPersonalKey(val);
    localStorage.setItem('personal_gemini_key', val);
  };

  const [atsScores, setATSScores] = useState({ before: null, after: null });
  const [sectionScores, setSectionScores] = useState({ before: {}, after: null });
  const [rewrittenResume, setRewrittenResume] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState({ analyze: false, rewrite: false });
  const [activeTab, setActiveTab] = useState('scores');
  const [history, setHistory] = useState([]);
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackRating, setFeedbackRating] = useState(0);
  const [feedbackReason, setFeedbackReason] = useState('');
  const [missingKeywords, setMissingKeywords] = useState([]);
  const [matchedKeywords, setMatchedKeywords] = useState([]);
  const [improvementTips, setImprovementTips] = useState([]);

  const analyzeResume = async () => {
    if (provider === 'personal_gemini' && !personalKey.trim()) {
      alert('Please enter your personal Gemini API key first.');
      return;
    }

    if (!resumeText.trim() || !jobDescription.trim()) {
      alert('Please fill in both resume and job description');
      return;
    }

    setLoading(prev => ({ ...prev, analyze: true }));
    // Reset after scores when re-analyzing
    setATSScores({ before: null, after: null });
    setSectionScores({ before: {}, after: null });
    setMissingKeywords([]);
    setMatchedKeywords([]);
    try {
      const response = await api.post('/resume/analyze', {
        resume_text: resumeText,
        job_description: jobDescription,
        provider: provider
      });

      setATSScores({ before: response.data.overall_score, after: null });
      setSectionScores({ before: response.data.section_scores, after: null });
      setMissingKeywords(response.data.missing_keywords || []);
      setMatchedKeywords(response.data.matched_keywords || []);
      setRewrittenResume(null);
      setSessionId(null);
    } catch (error) {
      alert('Analysis failed. Please check your API connection and try again.');
    } finally {
      setLoading(prev => ({ ...prev, analyze: false }));
    }
  };

  const rewriteResume = async () => {
    if (provider === 'personal_gemini' && !personalKey.trim()) {
      alert('Please enter your personal Gemini API key first.');
      return;
    }

    if (!resumeText.trim() || !jobDescription.trim()) {
      alert('Please fill in both resume and job description');
      return;
    }

    setLoading(prev => ({ ...prev, rewrite: true }));
    // Clear after scores while rewriting
    setATSScores(prev => ({ ...prev, after: null }));
    setSectionScores(prev => ({ ...prev, after: null }));
    try {
      const response = await api.post('/resume/rewrite', {
        resume_text: resumeText,
        job_description: jobDescription,
        provider: provider
      });

      const d = response.data;
      // Use ats_before from the SAME scoring run so Before/After are always consistent
      setATSScores({
        before: d.ats_before,
        after:  d.ats_after,
      });
      setSectionScores({
        before: d.section_scores_before,
        after:  d.section_scores_after,
      });
      setMissingKeywords(d.missing_keywords || []);
      setMatchedKeywords(d.matched_keywords || []);
      setImprovementTips(d.improvement_tips || []);
      setRewrittenResume(d.rewritten_json);
      setSessionId(d.session_id);
      // Stay on Scores tab so user immediately sees improvement
      setActiveTab('scores');

      loadHistory();
    } catch (error) {
      const msg = error?.response?.data?.detail || 'Rewrite failed. The AI service may be busy. Please try again.';
      alert(msg);
    } finally {
      setLoading(prev => ({ ...prev, rewrite: false }));
    }
  };

  const loadHistory = async () => {
    try {
      const response = await api.get('/history');
      setHistory(response.data);
    } catch (error) {
      console.error('Failed to load history:', error);
    }
  };

  const handleDownloadPDF = async () => {
    if (!sessionId) return;
    
    try {
      const response = await api.get(`/history/${sessionId}/export`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'resume.pdf');
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch (error) {
      alert('Failed to download PDF');
    }
  };

  const submitFeedback = async () => {
    if (!sessionId || feedbackRating === 0) return;
    
    try {
      await api.post('/resume/feedback', {
        session_id: sessionId,
        rating: feedbackRating,
        rating_reason: feedbackReason || null
      });
      setShowFeedback(false);
      setFeedbackRating(0);
      setFeedbackReason('');
      alert('Thank you for your feedback!');
    } catch (error) {
      alert('Failed to submit feedback');
    }
  };

  React.useEffect(() => {
    loadHistory();
  }, []);

  let step1State = 'active';
  let step2State = '';
  let step3State = '';

  if (atsScores.after !== null && atsScores.after !== undefined) {
    step1State = 'completed';
    step2State = 'completed';
    step3State = 'completed';
  } else if (atsScores.before !== null && atsScores.before !== undefined) {
    step1State = 'completed';
    step2State = 'completed';
    step3State = 'active';
  }

  const renderStep = (num, label, state, hasNext) => (
    <>
      <div className={`step ${state}`}>
        <div className="step-number">
          {state === 'completed' ? '✓' : num}
        </div>
        <div className="step-label">{label}</div>
      </div>
      {hasNext && <div className="step-line"></div>}
    </>
  );

  return (
    <div className="page-container">
      <div className="bg-circle-1"></div>
      <div className="bg-circle-2"></div>
      <div className="bg-circle-3"></div>
      <Navbar />
      
      <div className="dashboard-grid">
        <div style={{ gridColumn: '1 / -1' }}>
          <div style={{ maxWidth: '600px', margin: '40px auto 0', textAlign: 'center' }}>
            <div className="hero-badge animate-in" style={{ animationDelay: '0ms' }}>
              <span className="badge-dot"></span>
              AI-Powered Resume Optimizer
            </div>
            
            <h1 className="hero-title animate-in" style={{ animationDelay: '80ms' }}>
              Resume Optimizer
            </h1>
            
            <p className="hero-subtitle animate-in" style={{ animationDelay: '120ms', marginBottom: '16px' }}>
              Paste your resume and job description to begin
            </p>

            <div className="provider-selector-container animate-in" style={{ animationDelay: '140ms', margin: '0 auto 24px', maxWidth: '320px' }}>
              <label htmlFor="provider-select" className="provider-select-label" style={{ fontSize: '11px', fontWeight: '700', letterSpacing: '0.05em', color: 'var(--text-secondary)', marginRight: '8px' }}>
                AI PROVIDER:
              </label>
              <select
                id="provider-select"
                value={provider}
                onChange={handleProviderChange}
                className="provider-select"
              >
                <option value="gemini">Gemini (Cloud Rotation)</option>
                <option value="personal_gemini">Personal Gemini API Key</option>
                <option value="ollama">Ollama (Local / Offline)</option>
                <option value="openrouter">OpenRouter (Any Model API)</option>
              </select>
            </div>

            {provider === 'personal_gemini' && (
              <div className="personal-key-container animate-in">
                <div className="personal-key-label">
                  <span>Enter Gemini API Key</span>
                  {personalKey && (
                    <span className="personal-key-saved-badge">
                      ✓ Saved Locally
                    </span>
                  )}
                </div>
                <div className="personal-key-input-wrapper">
                  <input
                    type={showKey ? 'text' : 'password'}
                    placeholder="AIzaSy..."
                    value={personalKey}
                    onChange={handlePersonalKeyChange}
                    className="personal-key-input"
                  />
                  <button
                    type="button"
                    onClick={() => setShowKey(!showKey)}
                    className="personal-key-toggle-btn"
                    title={showKey ? 'Hide key' : 'Show key'}
                  >
                    {showKey ? (
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                        <line x1="1" y1="1" x2="23" y2="23"></line>
                      </svg>
                    ) : (
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                        <circle cx="12" cy="12" r="3"></circle>
                      </svg>
                    )}
                  </button>
                </div>
              </div>
            )}

            <div className="stepper animate-in" style={{ animationDelay: '160ms', justifyContent: 'center' }}>
              {renderStep(1, 'Paste Resume', step1State, true)}
              {renderStep(2, 'Analyze', step2State, true)}
              {renderStep(3, 'Rewrite & Export', step3State, false)}
            </div>
          </div>
        </div>

        <div className="dashboard-left">
          <ResumeInput 
            resumeText={resumeText}
            setResumeText={setResumeText}
            jobDescription={jobDescription}
            setJobDescription={setJobDescription}
            onAnalyze={analyzeResume}
            onRewrite={rewriteResume}
            loading={loading}
            canRewrite={atsScores.before !== null && atsScores.before !== undefined}
            provider={provider}
          />
        </div>

        <div className="dashboard-right animate-in" style={{ animationDelay: '320ms' }}>
          <div className="dash-panel-card">
            <div className="dash-panel-header">
              <div className="dash-tabs">
                <button 
                  onClick={() => setActiveTab('scores')}
                  className={`dash-tab-btn ${activeTab === 'scores' ? 'active' : ''}`}
                >
                  Scores
                </button>
                <button 
                  onClick={() => setActiveTab('preview')}
                  className={`dash-tab-btn ${activeTab === 'preview' ? 'active' : ''}`}
                >
                  Preview
                </button>
              </div>

              <button 
                onClick={handleDownloadPDF}
                disabled={!sessionId || loading.rewrite}
                aria-label="Export PDF"
                className="export-btn"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="7 10 12 15 17 10"></polyline>
                  <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                {loading.rewrite ? 'Exporting...' : 'Export PDF'}
              </button>
              {sessionId && (
                <button 
                  onClick={() => setShowFeedback(true)}
                  className="export-btn"
                  style={{ marginLeft: '8px' }}
                >
                  Rate
                </button>
              )}
            </div>

            <div className="dash-panel-body">
              {activeTab === 'scores' && (
                <ATSScoreCard
                  beforeScore={atsScores.before}
                  afterScore={atsScores.after}
                  sectionScoresBefore={sectionScores.before}
                  sectionScoresAfter={sectionScores.after}
                  missingKeywords={missingKeywords}
                  matchedKeywords={matchedKeywords}
                  improvementTips={improvementTips}
                  loading={loading.analyze || loading.rewrite}
                />
              )}
              
              {activeTab === 'preview' && (
                <RewrittenPreview 
                  resumeData={rewrittenResume}
                  loading={loading.analyze || loading.rewrite}
                />
              )}
            </div>
          </div>
        </div>
      </div>

      {showFeedback && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ padding: '24px', maxWidth: '400px' }}>
            <h3 style={{ marginBottom: '16px' }}>Rate this rewrite</h3>
            <p style={{ marginBottom: '16px', color: '#666' }}>
              How well did this resume match the job description?
            </p>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', justifyContent: 'center' }}>
              {[1, 2, 3, 4, 5].map(star => (
                <button
                  key={star}
                  onClick={() => setFeedbackRating(star)}
                  style={{
                    fontSize: '24px',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    color: star <= feedbackRating ? '#f59e0b' : '#ddd'
                  }}
                >
                  ★
                </button>
              ))}
            </div>
            <textarea
              placeholder="Optional: Why did you give this rating?"
              value={feedbackReason}
              onChange={(e) => setFeedbackReason(e.target.value)}
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                marginBottom: '16px',
                minHeight: '60px'
              }}
            />
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowFeedback(false)}
                style={{
                  padding: '8px 16px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  background: 'white',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
              <button
                onClick={submitFeedback}
                disabled={feedbackRating === 0}
                style={{
                  padding: '8px 16px',
                  border: 'none',
                  borderRadius: '4px',
                  background: feedbackRating === 0 ? '#ccc' : '#3b82f6',
                  color: 'white',
                  cursor: feedbackRating === 0 ? 'not-allowed' : 'pointer'
                }}
              >
                Submit
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

export default Dashboard;