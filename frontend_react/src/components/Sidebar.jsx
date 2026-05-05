import React from 'react';
import { PlusCircle, MessageSquare, Layers } from 'lucide-react';

export default function Sidebar({ projects, activeProjectId, activeView, onProjectSelect, onViewSelect, onNewProject, onGoHome }) {
  return (
    <div className="app-sidebar glass">
      <div className="sidebar-header" onClick={onGoHome} style={{ cursor: 'pointer' }}>
        <div className="logo-text">Developlus</div>
      </div>
      
      <div className="sidebar-content">
        <button className="new-project-btn" onClick={onNewProject}>
          <PlusCircle size={18} />
          <span>Start New Project</span>
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
                  <span>Chat View</span>
                </button>
                <div className="action-divider"></div>
                <button 
                  className={`action-btn ${activeProjectId === proj.id && activeView === 'stack' ? 'active' : ''}`}
                  onClick={() => { onProjectSelect(proj.id); onViewSelect('stack'); }}
                >
                  <Layers size={14} />
                  <span>Stack View</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      <div className="sidebar-footer" style={{ marginTop: 'auto', padding: '20px', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
        <button 
          className={`action-btn ${activeView === 'settings' ? 'active' : ''}`}
          onClick={() => { onProjectSelect(null); onViewSelect('settings'); }}
          style={{ width: '100%', justifyContent: 'center' }}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: '8px' }}><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
          <span>Settings</span>
        </button>
      </div>
    </div>
  );
}
