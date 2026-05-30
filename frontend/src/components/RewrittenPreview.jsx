import React, { useState } from 'react';
import './RewrittenPreview.css';

const RewrittenPreview = ({ resumeData }) => {
  const [copied, setCopied] = useState(false);

  if (!resumeData) return null;

  const cleanUrl = (url) => {
    if (!url) return '';
    const trimmed = url.trim();
    if (!trimmed) return '';
    if (trimmed.startsWith('http://') || trimmed.startsWith('https://') || trimmed.startsWith('mailto:') || trimmed.startsWith('tel:')) {
      return trimmed;
    }
    return `https://${trimmed}`;
  };

  const handleCopy = () => {
    // Basic text format copy could be extended, but stringify works over no copy
    navigator.clipboard.writeText(JSON.stringify(resumeData, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const SectionContainer = ({ title, children, className = '' }) => (
    <div className={`preview-section-card animate-in ${className}`} style={{ animationDelay: '100ms' }}>
      {title && (
        <h3 className="preview-section-title">
          {title}
        </h3>
      )}
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

      {resumeData.header && (
        <SectionContainer className="header-preview-card">
          <h2 className="preview-name">{resumeData.header.name}</h2>
          <div className="preview-contact-grid">
            {resumeData.header.email && (
              <span className="contact-item">
                <span className="contact-icon">📧</span>
                <a href={`mailto:${resumeData.header.email}`} className="link-text">{resumeData.header.email}</a>
              </span>
            )}
            {resumeData.header.phone && (
              <span className="contact-item">
                <span className="contact-icon">📞</span>
                <a href={`tel:${resumeData.header.phone}`} className="link-text">{resumeData.header.phone}</a>
              </span>
            )}
            {resumeData.header.linkedin && (
              <span className="contact-item">
                <span className="contact-icon">🔗</span>
                <a href={cleanUrl(resumeData.header.linkedin)} target="_blank" rel="noopener noreferrer" className="link-text">LinkedIn</a>
              </span>
            )}
            {resumeData.header.github && (
              <span className="contact-item">
                <span className="contact-icon">💻</span>
                <a href={cleanUrl(resumeData.header.github)} target="_blank" rel="noopener noreferrer" className="link-text">GitHub</a>
              </span>
            )}
            {resumeData.header.portfolio && (
              <span className="contact-item">
                <span className="contact-icon">🌐</span>
                <a href={cleanUrl(resumeData.header.portfolio)} target="_blank" rel="noopener noreferrer" className="link-text">Portfolio</a>
              </span>
            )}
            {resumeData.header.leetcode && (
              <span className="contact-item">
                <span className="contact-icon">⚡</span>
                <a href={cleanUrl(resumeData.header.leetcode)} target="_blank" rel="noopener noreferrer" className="link-text">LeetCode</a>
              </span>
            )}
          </div>
        </SectionContainer>
      )}

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
                    {project.url ? (
                      <a href={cleanUrl(project.url)} target="_blank" rel="noopener noreferrer" className="link-text" style={{ color: 'var(--accent)' }}>
                        {project.name}
                      </a>
                    ) : (
                      project.name
                    )}
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
                    {exp.url ? (
                      <a href={cleanUrl(exp.url)} target="_blank" rel="noopener noreferrer" className="link-text" style={{ color: 'var(--accent)' }}>
                        {exp.company}
                      </a>
                    ) : (
                      exp.company
                    )}
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
                {cert.url ? (
                  <a href={cleanUrl(cert.url)} target="_blank" rel="noopener noreferrer" className="link-text" style={{ color: 'var(--accent)', fontWeight: 500 }}>
                    {cert.name}
                  </a>
                ) : (
                  cert.name
                )}
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