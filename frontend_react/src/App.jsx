import { useState } from 'react';
import Sidebar from './components/Sidebar';
import ChatView from './components/ChatView';
import StackView from './components/StackView';
import { mockProjects, mockChatHistory, mockStackRecommendations } from './data/mockData';

export default function App() {
  const [projects, setProjects] = useState(mockProjects);
  const [activeProjectId, setActiveProjectId] = useState(mockProjects[0]?.id || null);
  const [activeView, setActiveView] = useState('chat'); // 'chat' | 'stack'

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
      const reply = { id: (Date.now() + 1).toString(), role: 'assistant', content: "Bu mock bir cevaptır. Arka plan bağlandığında gerçek LLM yanıtı buraya gelecek." };
      setChatHistories(prev => ({
        ...prev,
        [projectId]: [...(prev[projectId] || []), reply]
      }));
    }, 1000);
  };

  const handleNewProject = () => {
    const newId = `p${Date.now()}`;
    const newProj = { id: newId, name: `Yeni Proje ${projects.length + 1}`, createdAt: new Date().toISOString() };
    setProjects([newProj, ...projects]);
    setActiveProjectId(newId);
    setActiveView('chat');
  };

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
      />

      <main className="main-content">
        {activeProjectId ? (
          activeView === 'chat' ? (
            <ChatView 
              project={activeProject} 
              chatHistory={currentChatHistory} 
              onSendMessage={handleSendMessage} 
            />
          ) : (
            <StackView 
              project={activeProject} 
              recommendations={currentStack} 
            />
          )
        ) : (
          <div className="empty-app-state glass">
            <h2>Hoş Geldiniz</h2>
            <p>Başlamak için sol menüden "Yeni Projeye Başla" butonuna tıklayın veya mevcut bir projeyi seçin.</p>
          </div>
        )}
      </main>
    </div>
  );
}
