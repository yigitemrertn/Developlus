import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatView from './components/ChatView';
import StackView from './components/StackView';
import SurveyView from './components/SurveyView';
import AuthView from './components/AuthView';
import ProjectsView from './components/ProjectsView';
import SettingsView from './components/SettingsView';
// import { mockProjects, mockChatHistory, mockStackRecommendations } from './data/mockData';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [projects, setProjects] = useState([]);
  const [activeProjectId, setActiveProjectId] = useState(null);
  const [activeView, setActiveView] = useState('projects'); // 'chat' | 'stack' | 'survey' | 'projects' | 'settings'

  const [chatHistories, setChatHistories] = useState({});
  const [stackRecs, setStackRecs] = useState({});

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const res = await fetch('http://localhost:8000/auth/me', {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (res.ok) {
            setIsAuthenticated(true);
            fetchProjects(token);
          } else {
            localStorage.removeItem('access_token');
          }
        } catch (e) {
          console.error('Auth error:', e);
        }
      }
      setIsInitializing(false);
    };
    checkAuth();
  }, []);

  const fetchProjects = async (token) => {
    try {
      const res = await fetch('http://localhost:8000/projects', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        // Backend returns project_name, let's map it to 'name' for frontend compatibility
        const mapped = data.map(p => ({...p, name: p.project_name}));
        setProjects(mapped);
      }
    } catch (e) {
      console.error('Projects error:', e);
    }
  };

  const activeProject = projects.find(p => p.id === activeProjectId);
  const currentChatHistory = chatHistories[activeProjectId] || [];
  const currentStack = stackRecs[activeProjectId] || null;

  const handleSendMessage = (projectId, message) => {
    // Mock ekleme işlemi
    const newMsg = { id: Date.now().toString(), role: 'user', content: message };
    setChatHistories(prev => ({
      ...prev,
      [projectId]: [...(prev[projectId] || []), newMsg]
    }));

    // Mock AI cevabı
    setTimeout(() => {
      const reply = { id: (Date.now() + 1).toString(), role: 'assistant', content: "This is a mock response. When the backend is connected, the real LLM response will appear here." };
      setChatHistories(prev => ({
        ...prev,
        [projectId]: [...(prev[projectId] || []), reply]
      }));
    }, 1000);
  };

  const handleNewProject = () => {
    setActiveProjectId(null);
    setActiveView('survey');
  };

  const handleDeleteProject = async (id) => {
    const token = localStorage.getItem('access_token');
    try {
      const res = await fetch(`http://localhost:8000/projects/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setProjects(projects.filter(p => p.id !== id));
        if (activeProjectId === id) {
          setActiveProjectId(null);
          setActiveView('projects');
        }
      }
    } catch (e) {
      console.error('Delete failed:', e);
    }
  };

  const handleSurveyComplete = async (answers) => {
    const projName = answers.projectName || `New Project ${projects.length + 1}`;
    const token = localStorage.getItem('access_token');
    
    try {
      if (activeProjectId) {
        // Updating existing project survey
        const res = await fetch(`http://localhost:8000/projects/${activeProjectId}/survey`, {
          method: 'PUT',
          headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify(answers)
        });
        if (res.ok) {
          const updatedProjects = projects.map(p => 
            p.id === activeProjectId ? { ...p, survey_complete: true, name: projName } : p
          );
          setProjects(updatedProjects);
          setActiveView('chat');
        }
      } else {
        // Creating new project
        const createRes = await fetch('http://localhost:8000/projects', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ project_name: projName, description: 'Created via Survey' })
        });
        
        if (createRes.ok) {
          const newProjData = await createRes.json();
          const newId = newProjData.id;
          
          // Now save survey
          const surveyRes = await fetch(`http://localhost:8000/projects/${newId}/survey`, {
            method: 'PUT',
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify(answers)
          });
          
          if (surveyRes.ok) {
            const newProj = { ...newProjData, name: newProjData.project_name, survey_complete: true };
            setProjects([newProj, ...projects]);
            setActiveProjectId(newId);
            setActiveView('chat');
          }
        }
      }
    } catch (e) {
      console.error('Failed to save survey:', e);
    }
  };

  if (isInitializing) {
    return (
      <div className="app-root app-layout" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="glow-orb glow-1" />
        <div className="glow-orb glow-2" />
        <div style={{ zIndex: 10, color: 'var(--text-secondary)' }}>Yükleniyor...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <AuthView onLogin={() => {
      setIsAuthenticated(true);
      fetchProjects(localStorage.getItem('access_token'));
    }} />;
  }

  return (
    <div className="app-root app-layout" id="appRoot">
      <div className="noise-overlay" />
      <div className="glow-orb glow-1" />
      <div className="glow-orb glow-2" />
      <div className="glow-orb glow-3" />

      <Sidebar 
        projects={projects}
        activeProjectId={activeProjectId}
        activeView={activeView}
        onProjectSelect={setActiveProjectId}
        onViewSelect={setActiveView}
        onNewProject={handleNewProject}
        onGoHome={() => { setActiveProjectId(null); setActiveView('chat'); }}
      />

      <main className="main-content">
        {activeProjectId ? (
          activeView === 'chat' ? (
            <ChatView 
              project={activeProject} 
              chatHistory={currentChatHistory} 
              onSendMessage={handleSendMessage} 
              onGoToSurvey={() => setActiveView('survey')}
            />
          ) : (
            <StackView 
              project={activeProject} 
              recommendations={currentStack} 
            />
          )
        ) : activeView === 'survey' ? (
          <SurveyView 
            onComplete={handleSurveyComplete} 
            existingProject={activeProject} 
          />
        ) : activeView === 'settings' ? (
          <SettingsView />
        ) : (
          <ProjectsView 
            projects={projects}
            onProjectSelect={setActiveProjectId}
            onViewSelect={setActiveView}
            onNewProject={handleNewProject}
            onDeleteProject={handleDeleteProject}
          />
        )}
      </main>
    </div>
  );
}
