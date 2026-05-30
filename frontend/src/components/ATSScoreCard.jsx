import React, { useEffect, useState } from 'react';
import './ATSScoreCard.css';

/* ─── helpers ─────────────────────────────────────────────────── */
const r1 = (v) => Math.round(v * 10) / 10;   // round to 1 decimal

const scoreBand = (score) => {
  if (score === null || score === undefined) return 'band-none';
  if (score < 40)  return 'band-red';
  if (score < 70)  return 'band-amber';
  return 'band-green';
};

const scoreColor = (score) => {
  if (score === null || score === undefined) return 'var(--border)';
  if (score < 40)  return 'var(--accent-red)';
  if (score < 70)  return 'var(--accent-amber)';
  return 'var(--accent-green)';
};

/* ─── component ───────────────────────────────────────────────── */
const ATSScoreCard = ({
  beforeScore,
  afterScore,
  sectionScoresBefore,
  sectionScoresAfter,
  missingKeywords = [],
  matchedKeywords = [],
  improvementTips = [],
}) => {
  const [animatedBefore, setAnimatedBefore] = useState(0);
  const [animatedAfter,  setAnimatedAfter]  = useState(0);

  /* animate score rings */
  useEffect(() => {
    if (beforeScore == null) return;
    let cur = 0;
    const target = beforeScore;
    const inc = Math.ceil(target / 20) || 1;
    const t = setInterval(() => {
      cur += inc;
      if (cur >= target) { setAnimatedBefore(target); clearInterval(t); }
      else               { setAnimatedBefore(cur); }
    }, 50);
    return () => clearInterval(t);
  }, [beforeScore]);

  useEffect(() => {
    if (afterScore == null) return;
    let cur = 0;
    const target = afterScore;
    const inc = Math.ceil(target / 20) || 1;
    const t = setInterval(() => {
      cur += inc;
      if (cur >= target) { setAnimatedAfter(target); clearInterval(t); }
      else               { setAnimatedAfter(cur); }
    }, 50);
    return () => clearInterval(t);
  }, [afterScore]);

  /* SVG ring */
  const RADIUS        = 54;
  const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

  const renderRing = (score, animated, label) => {
    const missing = score == null;
    const offset  = missing
      ? CIRCUMFERENCE
      : CIRCUMFERENCE - ((animated || 0) / 100) * CIRCUMFERENCE;
    const color = scoreColor(score);

    return (
      <div className="ring-container">
        <div className="ring-svg-wrapper">
          <svg width="140" height="140" style={{ transform: 'rotate(-90deg)' }}>
            <circle cx="70" cy="70" r={RADIUS} fill="transparent"
              stroke="var(--bg-elevated)" strokeWidth="10" />
            <circle cx="70" cy="70" r={RADIUS} fill="transparent"
              stroke={color} strokeWidth="10"
              strokeDasharray={CIRCUMFERENCE} strokeDashoffset={offset}
              strokeLinecap="round"
              style={{ transition: 'stroke-dashoffset 0.1s linear, stroke 0.3s ease' }}
            />
          </svg>
          <div className="ring-score-text"
            style={{ color: missing ? 'var(--text-tertiary)' : 'var(--text-primary)' }}>
            {missing ? '--' : animated}
          </div>
        </div>
        <div className="ring-label">{label}</div>
      </div>
    );
  };

  const hasSections = sectionScoresBefore && Object.keys(sectionScoresBefore).length > 0;
  const hasMissing  = missingKeywords && missingKeywords.length > 0;
  const hasMatched  = matchedKeywords && matchedKeywords.length > 0;

  const SECTIONS = [
    { key: 'summary',        label: 'Summary' },
    { key: 'skills',         label: 'Skills' },
    { key: 'internship',     label: 'Internship' },
    { key: 'projects',       label: 'Projects' },
    { key: 'education',      label: 'Education' },
    { key: 'certifications', label: 'Certifications' },
  ];

  return (
    <div className="score-card-container">

      {/* ── Score rings ── */}
      <div className="score-rings-wrapper">
        {renderRing(beforeScore, animatedBefore, 'Before Rewrite')}
        {renderRing(afterScore,  animatedAfter,  'After Rewrite')}
      </div>

      {/* ── Section breakdown table ── */}
      {hasSections && (
        <div className="breakdown-section">
          <h3>Section Breakdown</h3>
          <div className="breakdown-table">
            <div className="breakdown-header">
              <div>Section</div>
              <div style={{ textAlign: 'center' }}>Before</div>
              <div style={{ textAlign: 'center' }}>After</div>
              <div style={{ textAlign: 'center' }}>Change</div>
            </div>

            {SECTIONS.map(({ key, label }) => {
              const before = r1(sectionScoresBefore?.[key] ?? 0);
              const after  = r1(sectionScoresAfter?.[key]  ?? 0);
              const change = r1(after - before);
              const absent = !sectionScoresBefore?.[key] && !sectionScoresAfter?.[key];
              const showAfterBar = sectionScoresAfter && sectionScoresAfter[key] != null;

              let changeColor = 'var(--text-tertiary)';
              let changeBg    = 'transparent';
              let symbol      = '—';
              if (change > 0)  { changeColor = 'var(--accent-green)'; changeBg = 'rgba(16,185,129,0.12)'; symbol = '↑'; }
              if (change < 0)  { changeColor = 'var(--accent-red)';   changeBg = 'rgba(239,68,68,0.12)';  symbol = '↓'; }

              return (
                <div key={key} className="breakdown-row">
                  <div className="breakdown-section-name">
                    {label}
                    {/* Mini score bar under the section name */}
                    <div className="section-mini-bar-track">
                      <div
                        className={`section-mini-bar-fill ${scoreBand(showAfterBar ? after : before)}`}
                        style={{ width: `${Math.min(showAfterBar ? after : before, 100)}%` }}
                      />
                    </div>
                  </div>

                  {/* Before score with colour band */}
                  <div className="breakdown-score">
                    {absent ? (
                      <span className="score-absent">—</span>
                    ) : (
                      <span className={`score-badge ${scoreBand(before)}`}>{before}%</span>
                    )}
                  </div>

                  {/* After score with colour band */}
                  <div className="breakdown-score">
                    {absent ? (
                      <span className="score-absent">—</span>
                    ) : (
                      <span className={`score-badge ${scoreBand(after)}`}>{after}%</span>
                    )}
                  </div>

                  {/* Change badge */}
                  <div className="breakdown-change-wrapper">
                    <div className="breakdown-change-badge"
                      style={{ background: changeBg, color: changeColor }}>
                      {absent ? '—' : `${symbol} ${Math.abs(r1(change))}%`}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Keyword coverage progress ── */}
      {(hasMatched || hasMissing) && (
        <div className="keyword-coverage-section">
          <div className="keyword-coverage-header">
            <h3>Keyword Coverage</h3>
            <span className="keyword-coverage-ratio">
              {matchedKeywords.length} / {matchedKeywords.length + missingKeywords.length} matched
            </span>
          </div>
          <div className="keyword-coverage-bar-track">
            <div
              className="keyword-coverage-bar-fill"
              style={{
                width: `${(matchedKeywords.length / Math.max(matchedKeywords.length + missingKeywords.length, 1)) * 100}%`,
                background: `linear-gradient(90deg, var(--accent-green), ${(matchedKeywords.length / Math.max(matchedKeywords.length + missingKeywords.length, 1)) > 0.6 ? 'var(--accent-green)' : 'var(--accent-amber)'})`
              }}
            />
          </div>
          <div className="keyword-coverage-pct">
            {Math.round((matchedKeywords.length / Math.max(matchedKeywords.length + missingKeywords.length, 1)) * 100)}% coverage
          </div>
        </div>
      )}

      {/* ── Missing keywords panel ── */}
      {hasMissing && (
        <div className="keywords-panel keywords-panel--missing">
          <div className="keywords-panel-header">
            <span className="keywords-panel-icon">⚠</span>
            <h4>Keywords Missing from Resume</h4>
            <span className="keywords-panel-hint">Add these to boost your ATS score</span>
          </div>
          <div className="keywords-list">
            {missingKeywords.slice(0, 20).map((kw) => (
              <span key={kw} className="keyword-chip keyword-chip--missing">{kw}</span>
            ))}
            {missingKeywords.length > 20 && (
              <span className="keyword-chip keyword-chip--more">+{missingKeywords.length - 20} more</span>
            )}
          </div>
        </div>
      )}

      {/* ── Matched keywords panel ── */}
      {hasMatched && (
        <div className="keywords-panel keywords-panel--matched">
          <div className="keywords-panel-header">
            <span className="keywords-panel-icon">✓</span>
            <h4>Keywords Matched</h4>
          </div>
          <div className="keywords-list">
            {matchedKeywords.slice(0, 25).map((kw) => (
              <span key={kw} className="keyword-chip keyword-chip--matched">{kw}</span>
            ))}
            {matchedKeywords.length > 25 && (
              <span className="keyword-chip keyword-chip--more">+{matchedKeywords.length - 25} more</span>
            )}
          </div>
        </div>
      )}

      {/* ── Improvement suggestions ── */}
      {improvementTips && improvementTips.length > 0 && (
        <div className="improvement-tips-panel">
          <div className="improvement-tips-header">
            <span className="improvement-tips-icon">💡</span>
            <h4>Improvement Suggestions</h4>
          </div>
          <ul className="improvement-tips-list">
            {improvementTips.map((tip, idx) => (
              <li key={idx} className="improvement-tip-item">
                <span className="tip-bullet">{tip.startsWith('Great') || tip.startsWith('Good') ? '🟢' : '🔶'}</span>
                <span>{tip}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

    </div>
  );
};

export default ATSScoreCard;