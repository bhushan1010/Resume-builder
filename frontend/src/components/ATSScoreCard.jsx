import React, { useEffect, useState } from 'react';

const ATSScoreCard = ({ beforeScore, afterScore, sectionScoresBefore, sectionScoresAfter }) => {
  const [animatedBeforeScore, setAnimatedBeforeScore] = useState(0);
  const [animatedAfterScore, setAnimatedAfterScore] = useState(0);

  // Animate scores when they change
  useEffect(() => {
    if (beforeScore !== null) {
      let current = 0;
      const target = beforeScore;
      const increment = Math.ceil(target / 20); // Animate over 20 frames
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
    if (afterScore !== null) {
      let current = 0;
      const target = afterScore;
      const increment = Math.ceil(target / 20); // Animate over 20 frames
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

  const getScoreColor = (score) => {
    if (score === null) return 'border-gray-300 bg-gray-50 text-gray-500';
    if (score < 40) return 'border-red-500 bg-red-50 text-red-500';
    if (score < 70) return 'border-amber-500 bg-amber-50 text-amber-500';
    return 'border-green-500 bg-green-50 text-green-500';
  };

  const getScoreLabel = (score) => {
    if (score === null) return 'N/A';
    return `${score}%`;
  };

  return (
    <div className="space-y-6">
      {/* Score Display */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {/* Before Score */}
        <div className={`p-4 rounded-lg ${getScoreColor(beforeScore)}`}>
          <h3 className="text-sm font-medium mb-2">Before Rewrite</h3>
          <div className="flex items-baseline">
            <span className="text-3xl font-bold">{getScoreLabel(beforeScore)}</span>
            <span className="ml-1 text-sm">/100</span>
          </div>
          <p className="mt-2 text-xs">{beforeScore === null ? 'No data' : `Score before optimization`}</p>
        </div>
        
        {/* After Score */}
        <div className={`p-4 rounded-lg ${getScoreColor(afterScore)}`}>
          <h3 className="text-sm font-medium mb-2">After Rewrite</h3>
          <div className="flex items-baseline">
            <span className="text-3xl font-bold">{getScoreLabel(afterScore)}</span>
            <span className="ml-1 text-sm">/100</span>
          </div>
          <p className="mt-2 text-xs">{afterScore === null ? 'No data' : `Score after optimization`}</p>
        </div>
      </div>

      {/* Section Breakdown */}
      {(Object.keys(sectionScoresBefore).length > 0 || Object.keys(sectionScoresAfter).length > 0) && (
        <div>
          <h3 className="text-sm font-medium mb-3">Section Breakdown</h3>
          <div className="space-y-2">
            {[ 
              { key: 'summary', label: 'Summary' },
              { key: 'education', label: 'Education' },
              { key: 'projects', label: 'Projects' },
              { key: 'internship', label: 'Internship' },
              { key: 'skills', label: 'Skills' },
              { key: 'certifications', label: 'Certifications' }
            ].map(section => {
              const before = sectionScoresBefore[section.key] ?? 0;
              const after = sectionScoresAfter[section.key] ?? 0;
              const change = after - before;
              const changeClass = change > 0 ? 'text-green-500' : change < 0 ? 'text-red-500' : 'text-gray-500';
              const changeIcon = change > 0 ? '↑' : change < 0 ? '↓' →;
              
              return (
                <div key={section.key} className="flex justify-between text-sm">
                  <span>{section.label}</span>
                  <div className="flex items-center space-x-2">
                    <span className="w-8 text-center">{before}%</span>
                    <span className="w-8 text-center">{after}%</span>
                    <span className={`${changeClass} w-8 text-center`}>
                      {changeIcon}
                    </span>
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