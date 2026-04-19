import React, { useState, useRef, useEffect } from 'react';
import './ResumeInput.css';
import axios from 'axios';

const ResumeInput = ({ 
  resumeText, setResumeText, 
  jobDescription, setJobDescription, 
  onAnalyze, onRewrite, 
  loading, canRewrite 
}) => {
  // Internal state for PDF upload
  const [activeInputTab, setActiveInputTab] = useState('pdf'); // 'pdf' | 'text'
  const [pdfFile, setPdfFile] = useState(null);
  const [pdfUploadState, setPdfUploadState] = useState('idle'); // 'idle' | 'uploading' | 'success' | 'error'
  const [confidenceInfo, setConfidenceInfo] = useState(null); // { confidence, confidence_label }
  const [extractionError, setExtractionError] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  
  // Refs for focusing textarea after tab switch
  const textareaRef = useRef(null);
  const dropZoneRef = useRef(null);

  // Handle file selection
  const handleFileSelect = async (file) => {
    // Validate file type
    if (file.type !== 'application/pdf') {
      setExtractionError('Please upload a PDF file.');
      setPdfUploadState('error');
      return;
    }
    
    // Validate file size (5MB)
    if (file.size > 5 * 1024 * 1024) {
      setExtractionError('File too large. Max size is 5MB.');
      setPdfUploadState('error');
      return;
    }

    setPdfFile(file);
    setPdfUploadState('uploading');
    setExtractionError(null);
    setConfidenceInfo(null);

    try {
      // Create FormData and send to backend
      const formData = new FormData();
      formData.append('pdf_file', file);
      
      const response = await axios.post('/resume/extract-pdf', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          // Assuming auth token is handled via cookies or axios interceptors
        }
      });
      
      const result = response.data;
      
      if (result.fallback_required) {
        // Set error and schedule tab switch
        setExtractionError(result.fallback_message);
        setPdfUploadState('error');
        
        // Switch to text tab after delay
        setTimeout(() => {
          setActiveInputTab('text');
          // Focus textarea after tab switch
          if (textareaRef.current) {
            textareaRef.current.focus();
          }
        }, 1500);
        return;
      }
      
      // Success case
      setResumeText(result.text);
      setConfidenceInfo({
        confidence: result.confidence,
        confidence_label: result.confidence_label
      });
      setPdfUploadState('success');
      
    } catch (error) {
      console.error('PDF extraction error:', error);
      setExtractionError('Upload failed. Please try again.');
      setPdfUploadState('error');
    }
  };

  // Handle file removal
  const handleRemoveFile = () => {
    setPdfFile(null);
    setPdfUploadState('idle');
    setConfidenceInfo(null);
    setExtractionError(null);
    setResumeText(''); // Clear extracted text
  };

  // Handle drag over
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  // Handle drag leave
  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  // Handle drop
  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  // Handle tab switching
  const handleTabSwitch = (tab) => {
    // When switching from text to pdf, if no file exists, show idle state
    if (tab === 'pdf' && !pdfFile) {
      setPdfUploadState('idle');
      setExtractionError(null);
      setConfidenceInfo(null);
    }
    
    setActiveInputTab(tab);
    
    // Focus textarea when switching to text tab
    if (tab === 'text' && textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  return (
    <div className="resume-input-container">
      {/* Tab Switcher */}
      <div className="tab-switcher">
        <button
          onClick={() => handleTabSwitch('pdf')}
          className={`tab-btn ${activeInputTab === 'pdf' ? 'active' : ''}`}
        >
          📄 Upload PDF
        </button>
        <button
          onClick={() => handleTabSwitch('text')}
          className={`tab-btn ${activeInputTab === 'text' ? 'active' : ''}`}
        >
          ✏️ Paste Text
        </button>
      </div>

      {/* PDF Tab Content */}
      {activeInputTab === 'pdf' && (
        <div 
          className={`pdf-drop-zone ${pdfUploadState}`} 
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          ref={dropZoneRef}
          onClick={() => {
            // Trigger file input click when drop zone is clicked
            const fileInput = dropZoneRef.current.querySelector('input[type="file"]');
            if (fileInput) fileInput.click();
          }}
        >
          {/* Hidden file input */}
          <input 
            type="file" 
            accept=".pdf" 
            style={{ display: 'none' }}
            onChange={(e) => {
              const file = e.target.files[0];
              if (file) handleFileSelect(file);
              e.target.value = ''; // Reset input
            }}
          />
          
          {/* IDLE State Content */}
          {pdfUploadState === 'idle' && !isDragOver && (
            <div className="drop-zone-content">
              <svg className="upload-icon" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
              </svg>
              <p className="primary-text">Drop your resume PDF here</p>
              <p className="secondary-text">or click to browse</p>
              <p className="constraint-text">PDF only · Max 5MB · Up to 2 pages</p>
            </div>
          )}
          
          {/* DRAG OVER State Content */}
          {isDragOver && (
            <div className="drop-zone-content">
              <svg className="upload-icon" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
              </svg>
              <p className="primary-text">Release to upload</p>
            </div>
          )}
          
          {/* UPLOADING State Content */}
          {pdfUploadState === 'uploading' && (
            <div className="drop-zone-content">
              <div className="spinner-ring"></div>
              <p className="uploading-text">Extracting resume...</p>
              <p className="uploading-subtext">This may take a few seconds</p>
            </div>
          )}
          
          {/* SUCCESS State Content */}
          {pdfUploadState === 'success' && (
            <>
              <div className="drop-zone-content success-state">
                <svg className="file-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="16" y1="13" x2="8" y2="13"></line>
                  <line x1="16" y1="17" x2="8" y2="17"></line>
                  <polyline points="10 9 9 9 8 9"></polyline>
                </svg>
                <div className="file-info">
                  <p className="filename">{pdfFile ? pdfFile.name : 'resume.pdf'}</p>
                  <p className="file-size">
                    {pdfFile ? 
                      (pdfFile.size / 1024 / 1024).toFixed(2) + ' MB' : 
                      '5 MB'}
                  </p>
                </div>
                <button className="remove-btn" onClick={handleRemoveFile}>×</button>
              </div>
              
              {/* Confidence Indicator */}
              {confidenceInfo && (
                <div className="confidence-pill">
                  {confidenceInfo.confidence === 'high' && (
                    <>
                      <span className="confidence-icon">✓</span>
                      <span className="confidence-text">{confidenceInfo.confidence_label}</span>
                    </>
                  )}
                  {confidenceInfo.confidence === 'medium' && (
                    <>
                      <span className="confidence-icon">⚠</span>
                      <span className="confidence-text">{confidenceInfo.confidence_label}</span>
                    </>
                  )}
                  {confidenceInfo.confidence === 'low' && (
                    <>
                      <span className="confidence-icon">⚠</span>
                      <span className="confidence-text">{confidenceInfo.confidence_label}</span>
                    </>
                  )}
                </div>
              )}
            </>
          )}
          
          {/* ERROR State Content */}
          {pdfUploadState === 'error' && (
            <div className="drop-zone-content error-state">
              <svg className="error-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
              <p className="error-message">{extractionError}</p>
              <p className="error-subtext">Please paste your resume text instead</p>
            </div>
          )}
        </div>
      )}

      {/* Paste Text Tab Content */}
      {activeInputTab === 'text' && (
        <>
          {/* Banner showing if text was populated from PDF */}
          {pdfFile && resumeText && (
            <div className="pasted-from-pdf-banner">
              ✓ Populated from your PDF — you can edit below
            </div>
          )}
          
          <textarea
            ref={textareaRef}
            value={resumeText}
            onChange={(e) => setResumeText(e.target.value)}
            placeholder="Paste your current resume content here..."
            className="input-textarea"
            style={{ minHeight: '320px' }}
          />
        </>
      )}

      {/* Job Description Section (unchanged) */}
      <div className="input-section">
        <div className="input-header">
          <svg className="input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
          Target Job Description
        </div>
        <textarea
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          placeholder="Paste the target job description here..."
          className="input-textarea"
          style={{ minHeight: '200px' }}
        />
      </div>

      {/* Action Buttons (unchanged) */}
      <div className="action-buttons">
        <button 
          onClick={onAnalyze} 
          disabled={loading.analyze || loading.rewrite}
          className="btn-analyze"
        >
          {loading.analyze ? (
            <>
              <div className="spin-ring" style={{ width: '16px', height: '16px', borderTopColor: 'var(--accent)' }}></div>
              Analyzing...
            </>
          ) : 'Analyze Match'}
        </button>

        <button 
          onClick={onRewrite} 
          disabled={!canRewrite || loading.analyze || loading.rewrite}
          className="btn-rewrite"
        >
          {loading.rewrite ? (
            <>
              <div className="spin-ring" style={{ width: '16px', height: '16px', borderTopColor: 'white' }}></div>
              Rewriting...
            </>
          ) : 'Rewrite Resume →'}
        </button>
      </div>
    </div>
  );
};

export default ResumeInput;