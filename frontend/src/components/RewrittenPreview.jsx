import React from 'react';

const RewrittenPreview = ({ resumeData }) => {
  if (!resumeData) return null;

  return (
    <div className="space-y-6">
      {/* Summary Section */}
      {resumeData.summary && (
        <div className="border-l-4 border-indigo-500 pl-4">
          <h3 className="text-lg font-semibold mb-2">Summary</h3>
          <p className="text-gray-700">{resumeData.summary}</p>
        </div>
      )}

      {/* Education Section */}
      {resumeData.education.length > 0 && (
        <div className="border-l-4 border-indigo-500 pl-4">
          <h3 className="text-lg font-semibold mb-2">Education</h3>
          <div className="space-y-4">
            {resumeData.education.map((edu, index) => (
              <div key={index} className="flex items-start">
                <div className="flex-shrink-0 w-20 text-sm text-gray-500">
                  {edu.duration}
                </div>
                <div className="flex-1">
                  <h4 className="font-medium">{edu.institution}</h4>
                  <p className="text-sm text-gray-600">{edu.degree}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Projects Section */}
      {resumeData.projects.length > 0 && (
        <div className="border-l-4 border-indigo-500 pl-4">
          <h3 className="text-lg font-semibold mb-2">Projects</h3>
          <div className="space-y-4">
            {resumeData.projects.map((project, index) => (
              <div key={index}>
                <h4 className="font-medium mb-1">
                  <a 
                    href={project.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-indigo-600 hover:underline"
                  >
                    {project.name}
                  </a>
                </h4>
                <p className="text-sm text-gray-500">{project.duration}</p>
                {project.bullets.length > 0 && (
                  <ul className="list-disc list-inside space-y-1 mt-2 text-sm text-gray-700">
                    {project.bullets.map((bullet, bulletIndex) => (
                      <li key={bulletIndex}>{bullet}</li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Internship/Experience Section */}
      {resumeData.internship.length > 0 && (
        <div className="border-l-4 border-indigo-500 pl-4">
          <h3 className="text-lg font-semibold mb-2">Internship & Experience</h3>
          <div className="space-y-4">
            {resumeData.internship.map((exp, index) => (
              <div key={index}>
                <div className="flex items-start">
                  <div className="flex-shrink-0 w-20 text-sm text-gray-500">
                    {exp.duration}
                  </div>
                  <div className="flex-1">
                    <h4 className="font-medium">
                      <a 
                        href={exp.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-indigo-600 hover:underline"
                      >
                        {exp.company}
                      </a>
                    </h4>
                    <p className="text-sm text-gray-600">{exp.role}</p>
                    {exp.bullets.length > 0 && (
                      <ul className="list-disc list-inside space-y-1 mt-2 text-sm text-gray-700">
                        {exp.bullets.map((bullet, bulletIndex) => (
                          <li key={bulletIndex}>{bullet}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Skills Section */}
      {resumeData.skills.length > 0 && (
        <div className="border-l-4 border-indigo-500 pl-4">
          <h3 className="text-lg font-semibold mb-2">Skills</h3>
          <div className="space-y-3">
            {resumeData.skills.map((skill, index) => (
              <div key={index} className="flex">
                <span className="flex-shrink-0 font-medium w-32">
                  {skill.category}:
                </span>
                <span className="flex-1">{skill.items}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Certifications Section */}
      {resumeData.certifications.length > 0 && (
        <div className="border-l-4 border-indigo-500 pl-4">
          <h3 className="text-lg font-semibold mb-2">Certifications</h3>
          <ul className="list-disc list-inside space-y-2">
            {resumeData.certifications.map((cert, index) => (
              <li key={index}>
                <a 
                  href={cert.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-indigo-600 hover:underline"
                >
                  {cert.name}
                </a>
                <span className="ml-2 text-sm text-gray-500">({cert.duration})</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default RewrittenPreview;