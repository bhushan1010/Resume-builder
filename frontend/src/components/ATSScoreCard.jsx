import React, { useEffect, useState } from 'react';
import './ATSScoreCard.css';

const ATSScoreCard = ({ beforeScore, afterScore, sectionScoresBefore, sectionScoresAfter }) => {
  const [animatedBeforeScore, setAnimatedBeforeScore] = useState(0);
  const [animatedAfterScore, setAnimatedAfterScore] = useState(0);

  // Animate scores when they change
  useEffect(() => {
    if (beforeScore !== null && beforeScore !== undefined) {
      let current = 0;
      const target = beforeScore;
      const increment = Math.ceil(target / 20) || 1; 
      const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
          setAnimatedBeforeScore(target);
          clearInterval(timer);
        } else {
          setAnimatedBeforeScore(current);
        }
      }, 50);

      return () => clearInterval(timer);
    }
  }, [beforeScore]);

  useEffect(() => {
    if (afterScore !== null && afterScore !== undefined) {
      let current = 0;
      const target = afterScore;
      const increment = Math.ceil(target / 20) || 1;
      const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
          setAnimatedAfterScore(target);
          clearInterval(timer);
        } else {
          setAnimatedAfterScore(current);
        }
      }, 50);

      return () => clearInterval(timer);
    }
  }, [afterScore]);

  const getScoreColorHex = (score) => {
    if (score === null || score === undefined) return 'var(--border)';
    if (score < 40) return 'var(--accent-red)';
    if (score < 70) return 'var(--accent-amber)';
    return 'var(--accent-green)';
  };

  const ringRadius = 54;
  const ringCircumference = 2 * Math.PI * ringRadius;

  const renderRing = (score, animatedScore, label) => {
    const isMissing = score === null || score === undefined;
    const offset = isMissing ? ringCircumference : ringCircumference - ((animatedScore || 0) / 100) * ringCircumference;
    const color = getScoreColorHex(score);

    return (
      <div className="ring-container">
        <div className="ring-svg-wrapper">
          <svg width="140" height="140" style={{ transform: 'rotate(-90deg)' }}>
            <circle
              cx="70"
              cy="70"
              r={ringRadius}
              fill="transparent"
              stroke="var(--bg-elevated)"
              strokeWidth="10"
            />
            <circle
              cx="70"
              cy="70"
              r={ringRadius}
              fill="transparent"
              stroke={color}
              strokeWidth="10"
              strokeDasharray={ringCircumference}
              strokeDashoffset={offset}
              strokeLinecap="round"
              style={{ transition: 'stroke-dashoffset 0.1s linear, stroke 0.3s ease' }}
            />
          </svg>
          <div 
            className="ring-score-text"
            style={{ color: isMissing ? 'var(--text-tertiary)' : 'var(--text-primary)' }}
          >
            {isMissing ? '--' : animatedScore}
          </div>
        </div>
        <div className="ring-label">
          {label}
        </div>
      </div>
    );
  };

  return (
    <div className="score-card-container">
      <div className="score-rings-wrapper">
        {renderRing(beforeScore, animatedBeforeScore, 'Before Rewrite')}
        {renderRing(afterScore, animatedAfterScore, 'After Rewrite')}
      </div>

      {(sectionScoresBefore && Object.keys(sectionScoresBefore).length > 0) && (
        <div className="breakdown-section">
          <h3>Section Breakdown</h3>
          <div className="breakdown-table">
            <div className="breakdown-header">
              <div>Section</div>
              <div style={{ textAlign: 'center' }}>Before</div>
              <div style={{ textAlign: 'center' }}>After</div>
              <div style={{ textAlign: 'center' }}>Change</div>
            </div>
            
            {[
              { key: 'summary', label: 'Summary' },
              { key: 'education', label: 'Education' },
              { key: 'projects', label: 'Projects' },
              { key: 'internship', label: 'Internship' },
              { key: 'skills', label: 'Skills' },
              { key: 'certifications', label: 'Certifications' }
            ].map(section => {
              const before = sectionScoresBefore?.[section.key] ?? 0;
              const after = sectionScoresAfter?.[section.key] ?? 0;
              const change = after - before;
              
              let changeColor = 'var(--text-tertiary)';
              let changeBg = 'transparent';
              let symbol = '—';
              
              if (change > 0) {
                changeColor = 'var(--accent-green)';
                changeBg = 'rgba(16, 185, 129, 0.1)';
                symbol = '↑';
              } else if (change < 0) {
                changeColor = 'var(--accent-red)';
                changeBg = 'rgba(239, 68, 68, 0.1)';
                symbol = '↓';
              }

              return (
                <div key={section.key} className="breakdown-row">
                  <div className="breakdown-section-name">{section.label}</div>
                  <div className="breakdown-score">{before}%</div>
                  <div className="breakdown-score">{after}%</div>
                  <div className="breakdown-change-wrapper">
                    <div 
                      className="breakdown-change-badge"
                      style={{ background: changeBg, color: changeColor }}
                    >
                      {symbol} {Math.abs(change)}%
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default ATSScoreCard;