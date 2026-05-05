import React from 'react';
import { PlusCircle, MessageSquare, Layers } from 'lucide-react';

export default function Sidebar({ projects, activeProjectId, activeView, onProjectSelect, onViewSelect, onNewProject }) {
  return (
    <div className="app-sidebar glass">
      <div className="sidebar-header">
        <div className="logo-text">Developlus</div>
      </div>
      
      <div className="sidebar-content">
        <button className="new-project-btn" onClick={onNewProject}>
          <PlusCircle size={18} />
          <span>Yeni Projeye Başla</span>
        </button>

        <div className="project-list">
          {projects.map((proj) => (
            <div key={proj.id} className={`project-card ${activeProjectId === proj.id ? 'active' : ''}`}>
              <div className="project-name" onClick={() => onProjectSelect(proj.id)}>
                {proj.name}
              </div>
              <div className="project-actions">
                <button 
                  className={`action-btn ${activeProjectId === proj.id && activeView === 'chat' ? 'active' : ''}`}
                  onClick={() => { onProjectSelect(proj.id); onViewSelect('chat'); }}
                >
                  <MessageSquare size={14} />
                  <span>Chat Görünümü</span>
                </button>
                <div className="action-divider"></div>
                <button 
                  className={`action-btn ${activeProjectId === proj.id && activeView === 'stack' ? 'active' : ''}`}
                  onClick={() => { onProjectSelect(proj.id); onViewSelect('stack'); }}
                >
                  <Layers size={14} />
                  <span>Stack Görünümü</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
