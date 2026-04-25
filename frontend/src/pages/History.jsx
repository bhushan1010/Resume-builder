import React, { useState, useEffect } from 'react';
import api from '../api/client';
import Navbar from '../components/Navbar';
import HistoryCard from '../components/HistoryCard';
import './History.css';

function History() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const response = await api.get('/history');
      setHistory(response.data);
    } catch (error) {
      console.error('Failed to load history:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  return (
    <div className="page-container">
      <div className="bg-circle-1"></div>
      <div className="bg-circle-2"></div>
      <div className="bg-circle-3"></div>
      <Navbar />
      
      <div className="page-header" style={{ marginBottom: '40px' }}>
        <h1 className="page-title">Optimization History</h1>
        <p className="page-subtitle">{history.length} sessions saved</p>
      </div>

      <div className="history-page-wrapper">
        {loading ? (
          <div className="history-loading">
            <div className="spin-ring" style={{ width: '32px', height: '32px', margin: '0 auto', borderTopColor: 'var(--accent)' }}></div>
            <p>Loading history...</p>
          </div>
        ) : history.length === 0 ? (
          <div className="history-empty-state animate-in">
            <svg className="history-empty-icon" width="48" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
            <p>No sessions yet. Head to the dashboard to get started.</p>
            <a href="/dashboard" className="btn-primary" style={{ textDecoration: 'none', display: 'inline-flex', width: 'auto', padding: '0 24px' }}>
              Go to Dashboard
            </a>
          </div>
        ) : (
          <div className="history-list">
            {history.map((session, index) => (
              <div key={session.id} style={{ animationDelay: `${index * 50}ms` }} className="animate-in">
                <HistoryCard session={session} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default History;