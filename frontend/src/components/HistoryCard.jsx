import React, { useState } from 'react';
import api from '../api/client';
import './HistoryCard.css';

const HistoryCard = ({ session }) => {
  const handleDownloadPDF = async () => {
    try {
      const response = await api.post(`/history/${session.id}/export`, {}, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `resume_${session.id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch (error) {
      alert('Failed to download PDF');
    }
  };

  const getScoreColor = (score) => {
    if (score < 40) return { bg: 'rgba(239, 68, 68, 0.1)', text: 'var(--accent-red)' };
    if (score < 70) return { bg: 'rgba(245, 158, 11, 0.1)', text: 'var(--accent-amber)' };
    return { bg: 'rgba(16, 185, 129, 0.1)', text: 'var(--accent-green)' };
  };

  const scoreColor = getScoreColor(session.ats_score_after);

  const formattedDate = new Date(session.created_at).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });

  const jdSnippet = session.job_description && session.job_description.length > 80 
    ? session.job_description.substring(0, 80) + '...'
    : session.job_description || 'No Job Description';

  return (
    <div className="history-card animate-in">
      <div className="history-card-date">
        {formattedDate}
      </div>
      
      <div className="history-card-jd">
        {jdSnippet}
      </div>
      
      <div className="history-card-actions">
        <div 
          className="history-card-score"
          style={{ background: scoreColor.bg, color: scoreColor.text }}
        >
          {session.ats_score_before}% → {session.ats_score_after}%
        </div>
        
        <button
          onClick={handleDownloadPDF}
          title="Download PDF"
          className="history-card-download-btn"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
        </button>
      </div>
    </div>
  );
};

export default HistoryCard;