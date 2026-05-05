import React from 'react';
import { PlusCircle, Trash2, CheckCircle, Clock } from 'lucide-react';

export default function ProjectsView({ projects, onProjectSelect, onViewSelect, onNewProject, onDeleteProject }) {
  const handleProjectClick = (proj) => {
    onProjectSelect(proj.id);
    if (proj.surveyCompleted) {
      onViewSelect('chat');
    } else {
      onViewSelect('survey');
    }
  };

  return (
    <div className="view-container projects-view glass">
      <div className="view-header flex-between">
        <div>
          <h2>Your Projects</h2>
          <p className="subtitle">Manage your technology stacks and AI consultations</p>
        </div>
        <button className="survey-nav-btn primary" onClick={onNewProject}>
          <PlusCircle size={18} />
          <span>New Project</span>
        </button>
      </div>

      <div className="projects-grid">
        {projects.length === 0 ? (
          <div className="empty-state">
            <p>No projects found. Create one to get started.</p>
          </div>
        ) : (
          projects.map((proj) => (
            <div key={proj.id} className="project-card-large glass">
              <div className="project-card-header" onClick={() => handleProjectClick(proj)}>
                <h3>{proj.name}</h3>
                <span className={`status-badge ${proj.surveyCompleted ? 'completed' : 'pending'}`}>
                  {proj.surveyCompleted ? <CheckCircle size={14} /> : <Clock size={14} />}
                  {proj.surveyCompleted ? 'Survey Completed' : 'Survey Pending'}
                </span>
              </div>
              <div className="project-card-footer">
                <span className="date-text">
                  Created: {new Date(proj.createdAt).toLocaleDateString()}
                </span>
                <button 
                  className="icon-btn delete-btn" 
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteProject(proj.id);
                  }}
                  title="Delete Project"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
