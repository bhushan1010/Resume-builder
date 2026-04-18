import React, { useState } from 'react';
import api from '../api/client';
import ResumeInput from '../components/ResumeInput';
import ATSScoreCard from '../components/ATSScoreCard';
import RewrittenPreview from '../components/RewrittenPreview';
import HistoryCard from '../components/HistoryCard';

function Dashboard() {
  const [resumeText, setResumeText] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [atsScores, setATSScores] = useState({ before: null, after: null });
  const [sectionScores, setSectionScores] = useState({ before: {}, after: null });
  const [rewrittenResume, setRewrittenResume] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState({ analyze: false, rewrite: false });
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
      
      // Also update history
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

  // Load history on mount
  React.useEffect(() => {
    loadHistory();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="border-4 border-dashed border-gray-200 rounded-lg h-full">
            <div className="flex flex-col items-center justify-between px-6 pt-14 pb-16 space-y-10 sm:flex-row sm:space-y-0 sm:space-x-10">
              <div className="space-y-6 text-center">
                <h2 className="text-base font-semibold text-indigo-600">
                  ATS Resume Rewriter
                </h2>
                <p className="mt-1 text-sm text-gray-600">
                  Optimize your resume for Applicant Tracking Systems
                </p>
              </div>
              
              <div className="hidden sm:block">
                <div className="relative h-48 w-48">
                  <svg className="absolute inset-0" viewBox="0 0 64 64" aria-hidden="true">
                    <defs>
                      <linearGradient id="gradient" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stopColor="#4f46e5" />
                        <stop offset="100%" stopColor="#7c3aed" />
                      </linearGradient>
                    </defs>
                    <circle cx="32" cy="32" r="30" stroke="url(#gradient)" strokeWidth="2" fill="none" />
                    <path 
                      d="M32 4l2.929 2.929M5.758 5.758l12.242 12.242M20.485 43.515l12.242-12.242M57.071 57.071l-2.929-2.929"
                      stroke="url(#gradient)" 
                      strokeWidth="2" 
                      strokeLinecap="round"
                    />
                  </svg>
                  <p className="mt-6 text-center text-sm font-medium text-gray-600">
                    Upload & Optimize
                  </p>
                </div>
              </div>
              
              <div className="w-full space-y-6">
                <ResumeInput 
                  resumeText={resumeText}
                  setResumeText={setResumeText}
                  jobDescription={jobDescription}
                  setJobDescription={setJobDescription}
                  onAnalyze={analyzeResume}
                  onRewrite={rewriteResume}
                  loading={loading}
                  canRewrite={Boolean(atsScores.before)}
                />
                
                {!atsScores.before && !atsScores.after ? (
                  <div className="text-center py-8">
                    <p className="text-gray-500">
                      Analyze your resume to see ATS scores
                    </p>
                  </div>
                ) : (
                  <>
                    <ATSScoreCard 
                      beforeScore={atsScores.before} 
                      afterScore={atsScores.after}
                      sectionScoresBefore={sectionScores.before}
                      sectionScoresAfter={sectionScores.after}
                    />
                    
                    {rewrittenResume && (
                      <div className="mt-6">
                        <RewrittenPreview resumeData={rewrittenResume} />
                        <button 
                          onClick={handleDownloadPDF}
                          disabled={loading.rewrite}
                          className="mt-4 w-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:offset-2"
                        >
                          {loading.rewrite ? 'Generating PDF...' : 'Download PDF'}
                        </button>
                      </div>
                    )}
                    
                    {!rewrittenResume && atsScores.before && (
                      <div className="text-center py-8">
                        <p className="text-gray-500">
                          Click "Rewrite" to generate an optimized resume
                        </p>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* History Section */}
      <div className="mt-8">
        <h2 className="sr-only">History</h2>
        <div className="space-y-4">
          {history.length > 0 ? (
            history.map((session) => (
              <HistoryCard 
                key={session.id} 
                session={session} 
              />
            ))
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-500">
                No history yet. Analyze and rewrite resumes to see them here.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;