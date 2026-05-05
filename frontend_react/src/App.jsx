import { useState } from 'react';
import Sidebar from './components/Sidebar';
import ChatView from './components/ChatView';
import StackView from './components/StackView';
import SurveyView from './components/SurveyView';
import AuthView from './components/AuthView';
import ProjectsView from './components/ProjectsView';
import SettingsView from './components/SettingsView';
import { mockProjects, mockChatHistory, mockStackRecommendations } from './data/mockData';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [projects, setProjects] = useState(mockProjects.map(p => ({ ...p, surveyCompleted: true })));
  const [activeProjectId, setActiveProjectId] = useState(null);
  const [activeView, setActiveView] = useState('projects'); // 'chat' | 'stack' | 'survey' | 'projects' | 'settings'

  const [chatHistories, setChatHistories] = useState(mockChatHistory);
  const [stackRecs, setStackRecs] = useState(mockStackRecommendations);

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

  const handleDeleteProject = (id) => {
    setProjects(projects.filter(p => p.id !== id));
    if (activeProjectId === id) {
      setActiveProjectId(null);
      setActiveView('projects');
    }
  };

  const handleSurveyComplete = (answers) => {
    const projName = answers.projectName || `New Project ${projects.length + 1}`;
    
    if (activeProjectId) {
      // Updating existing project survey
      const updatedProjects = projects.map(p => 
        p.id === activeProjectId ? { ...p, surveyCompleted: true, name: projName } : p
      );
      setProjects(updatedProjects);
      setActiveView('chat');
    } else {
      // Creating new project
      const newId = `p${Date.now()}`;
      const newProj = { id: newId, name: projName, createdAt: new Date().toISOString(), surveyCompleted: true };
      setProjects([newProj, ...projects]);
      setActiveProjectId(newId);
      setActiveView('chat');
    }
  };

  if (!isAuthenticated) {
    return <AuthView onLogin={() => setIsAuthenticated(true)} />;
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
