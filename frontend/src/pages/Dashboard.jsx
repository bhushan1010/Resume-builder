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
  const [atsScores, setATSScores] = useState({ before: null, after: null });
  const [sectionScores, setSectionScores] = useState({ before: {}, after: null });
  const [rewrittenResume, setRewrittenResume] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState({ analyze: false, rewrite: false });
  const [activeTab, setActiveTab] = useState('scores');
  const [history, setHistory] = useState([]);

  const analyzeResume = async () => {
    if (!resumeText.trim() || !jobDescription.trim()) {
      alert('Please fill in both resume and job description');
      return;
    }

    setLoading(prev => ({ ...prev, analyze: true }));
    try {
      const response = await api.post('/resume/analyze', {
        resume_text: resumeText,
        job_description: jobDescription
      });
      
      setATSScores({ before: response.data.overall_score, after: null });
      setSectionScores({ before: response.data.section_scores, after: null });
      setRewrittenResume(null);
      setSessionId(null);
    } catch (error) {
      alert('Analysis failed. Please try again.');
    } finally {
      setLoading(prev => ({ ...prev, analyze: false }));
    }
  };

  const rewriteResume = async () => {
    if (!resumeText.trim() || !jobDescription.trim()) {
      alert('Please fill in both resume and job description');
      return;
    }

    setLoading(prev => ({ ...prev, rewrite: true }));
    try {
      const response = await api.post('/resume/rewrite', {
        resume_text: resumeText,
        job_description: jobDescription
      });
      
      setATSScores(prev => ({ 
        ...prev, 
        after: response.data.ats_after 
      }));
      setSectionScores(prev => ({ 
        ...prev, 
        after: response.data.section_scores_after 
      }));
      setRewrittenResume(response.data.rewritten_json);
      setSessionId(response.data.session_id);
      setActiveTab('preview');  // auto-switch to show results
      
      loadHistory();
    } catch (error) {
      alert('Rewrite failed. Please try again.');
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
      const response = await api.post(`/history/${sessionId}/export`, {}, {
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
            
            <p className="hero-subtitle animate-in" style={{ animationDelay: '120ms' }}>
              Paste your resume and job description to begin
            </p>

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
                className="export-btn"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="7 10 12 15 17 10"></polyline>
                  <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                {loading.rewrite ? 'Exporting...' : 'Export PDF'}
              </button>
            </div>

            <div className="dash-panel-body">
              {activeTab === 'scores' && (
                <ATSScoreCard 
                  beforeScore={atsScores.before} 
                  afterScore={atsScores.after}
                  sectionScoresBefore={sectionScores.before}
                  sectionScoresAfter={sectionScores.after}
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

    </div>
  );
}

export default Dashboard;