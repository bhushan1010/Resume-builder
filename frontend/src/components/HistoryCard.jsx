import React, { useState } from 'react';
import api from '../api/client';

const HistoryCard = ({ session }) => {
  const [expanded, setExpanded] = useState(false);

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

  return (
    <div className="bg-white rounded-lg shadow border border-gray-200">
      <div className="px-6 py-4">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-lg font-medium text-gray-900">
              Resume Optimization
            </h3>
            <p className="text-sm text-gray-500">
              {new Date(session.created_at).toLocaleDateString()}
            </p>
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-indigo-500 hover:text-indigo-700"
          >
            {expanded ? '▲' : '▼'}
          </button>
        </div>
        
        <div className="mt-4 flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-700">
              JD: {session.job_description}
            </p>
            <div className="flex space-x-3">
              <span className="px-2 py-1 text-xs rounded-full 
                ${session.ats_score_before < 40 ? 'bg-red-100 text-red-800' 
                  : session.ats_score_before < 70 ? 'bg-amber-100 text-amber-800'
                  : 'bg-green-100 text-green-800'}">
                Before: {session.ats_score_before}%
              </span>
              <span className="px-2 py-1 text-xs rounded-full 
                ${session.ats_score_after < 40 ? 'bg-red-100 text-red-800' 
                  : session.ats_score_after < 70 ? 'bg-amber-100 text-amber-800'
                  : 'bg-green-100 text-green-800'}">
                After: {session.ats_score_after}%
              </span>
            </div>
          </div>
          
          <button
            onClick={handleDownloadPDF}
            className="mt-2 sm:mt-0 px-3 py-1 text-xs font-medium text-white 
              bg-indigo-600 hover:bg-indigo-700 rounded"
          >
            Download PDF
          </button>
        </div>
      </div>
      
      {expanded && (
        <div className="border-t border-gray-200">
          <div className="px-6 py-4">
            <h3 className="text-lg font-medium mb-3 text-gray-900">
              Rewritten Resume Preview
            </h3>
            <div className="space-y-4">
              {/* Summary */}
              <div>
                <h4 className="font-medium mb-1">Summary</h4>
                <p className="text-gray-700">
                  {/* This would normally show the rewritten summary,
                      but we don't have it in the history session data.
                      In a real app, we'd fetch the full session details */}
                  [Summary preview would appear here]
                </p>
              </div>
              
              {/* Skills */}
              <div>
                <h4 className="font-medium mb-1">Skills</h4>
                <p className="text-gray-700">
                  [Skills preview would appear here]
                </p>
              </div>
              
              {/* Experience */}
              <div>
                <h4 className="font-medium mb-1">Experience</h4>
                <p className="text-gray-700">
                  [Experience preview would appear here]
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HistoryCard;