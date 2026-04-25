import React, { useState } from 'react';
import './RewrittenPreview.css';

const RewrittenPreview = ({ resumeData }) => {
  const [copied, setCopied] = useState(false);

  if (!resumeData) return null;

  const handleCopy = () => {
    // Basic text format copy could be extended, but stringify works over no copy
    navigator.clipboard.writeText(JSON.stringify(resumeData, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const SectionContainer = ({ title, children }) => (
    <div className="preview-section-card animate-in" style={{ animationDelay: '100ms' }}>
      <h3 className="preview-section-title">
        {title}
      </h3>
      {children}
    </div>
  );

  const BulletList = ({ bullets }) => {
    if (!bullets || bullets.length === 0) return null;
    return (
      <ul className="preview-bullet-list">
        {bullets.map((bullet, idx) => (
          <li key={idx} className="preview-bullet-item">
            <span className="preview-bullet-icon">•</span>
            <span>{bullet}</span>
          </li>
        ))}
      </ul>
    );
  };

  return (
    <div className="preview-container">
      <div className="preview-header">
        <button onClick={handleCopy} aria-label="Copy JSON" className="copy-btn">
          {copied ? (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
              Copied!
            </>
          ) : (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
              Copy JSON
            </>
          )}
        </button>
      </div>

      {resumeData.summary && (
        <SectionContainer title="Summary">
          <p className="preview-text">{resumeData.summary}</p>
        </SectionContainer>
      )}

      {resumeData.education && resumeData.education.length > 0 && (
        <SectionContainer title="Education">
          <div>
            {resumeData.education.map((edu, index) => (
              <div key={index} className="preview-entry">
                <div className="preview-entry-duration">
                  {edu.duration}
                </div>
                <div className="preview-entry-content">
                  <h4 className="preview-entry-title">{edu.institution}</h4>
                  <p className="preview-entry-subtitle">{edu.degree}</p>
                </div>
              </div>
            ))}
          </div>
        </SectionContainer>
      )}

      {resumeData.projects && resumeData.projects.length > 0 && (
        <SectionContainer title="Projects">
          <div>
            {resumeData.projects.map((project, index) => (
              <div key={index} className="preview-entry" style={{ flexDirection: 'column', gap: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                  <h4 className="preview-entry-title">
                    <a href={project.url} target="_blank" rel="noopener noreferrer" className="link-text" style={{ color: 'var(--accent)' }}>
                      {project.name}
                    </a>
                  </h4>
                  <span className="preview-entry-duration" style={{ width: 'auto', textAlign: 'right' }}>{project.duration}</span>
                </div>
                <BulletList bullets={project.bullets} />
              </div>
            ))}
          </div>
        </SectionContainer>
      )}

      {resumeData.internship && resumeData.internship.length > 0 && (
        <SectionContainer title="Experience">
          <div>
            {resumeData.internship.map((exp, index) => (
              <div key={index} className="preview-entry">
                <div className="preview-entry-duration">
                  {exp.duration}
                </div>
                <div className="preview-entry-content">
                  <h4 className="preview-entry-title">
                    <a href={exp.url} target="_blank" rel="noopener noreferrer" className="link-text" style={{ color: 'var(--accent)' }}>
                      {exp.company}
                    </a>
                  </h4>
                  <p className="preview-entry-subtitle">{exp.role}</p>
                  <BulletList bullets={exp.bullets} />
                </div>
              </div>
            ))}
          </div>
        </SectionContainer>
      )}

      {resumeData.skills && resumeData.skills.length > 0 && (
        <SectionContainer title="Skills">
          <div>
            {resumeData.skills.map((skill, index) => (
              <div key={index} className="preview-skill-row">
                <div className="preview-skill-cat">
                  {skill.category}
                </div>
                <div className="preview-skill-items">{skill.items}</div>
              </div>
            ))}
          </div>
        </SectionContainer>
      )}

      {resumeData.certifications && resumeData.certifications.length > 0 && (
        <SectionContainer title="Certifications">
          <div>
            {resumeData.certifications.map((cert, index) => (
              <div key={index} className="preview-cert-row">
                <span className="preview-bullet-icon">•</span>
                <a href={cert.url} target="_blank" rel="noopener noreferrer" className="link-text" style={{ color: 'var(--accent)', fontWeight: 500 }}>
                  {cert.name}
                </a>
                <span className="preview-entry-duration" style={{ width: 'auto', marginLeft: '8px' }}>
                  ({cert.duration})
                </span>
              </div>
            ))}
          </div>
        </SectionContainer>
      )}
    </div>
  );
};

export default RewrittenPreview;