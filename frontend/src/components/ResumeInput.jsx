import React from 'react';

const ResumeInput = ({ resumeText, setResumeText, jobDescription, setJobDescription, onAnalyze, onRewrite, loading, canRewrite }) => {
  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Resume Text
        </label>
        <textarea
          value={resumeText}
          onChange={(e) => setResumeText(e.target.value)}
          placeholder="Paste your resume here..."
          className="w-full min-h-[300px] px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          rows={10}
          disabled={loading.analyze || loading.rewrite}
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Job Description
        </label>
        <textarea
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          placeholder="Paste job description here..."
          className="w-full min-h-[200px] px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          rows={6}
          disabled={loading.analyze || loading.rewrite}
        />
      </div>
      
      <div className="flex flex-col sm:flex-row sm:space-x-4">
        <button
          onClick={onAnalyze}
          disabled={loading.analyze || !resumeText.trim() || !jobDescription.trim()}
          className="w-full sm:w-auto flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:offset-2"
        >
          {loading.analyze ? 'Analyzing...' : 'Analyze'}
        </button>
        
        <button
          onClick={onRewrite}
          disabled={loading.rewrite || !canRewrite || !resumeText.trim() || !jobDescription.trim()}
          className="w-full sm:w-auto flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:offset-2"
        >
          {loading.rewrite ? 'Rewriting...' : 'Rewrite'}
        </button>
      </div>
    </div>
  );
};

export default ResumeInput;