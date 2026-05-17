import React, { useEffect, useState } from 'react';
import { getLatestStack } from '../api/analyzeApi';

const LayerIcon = ({ type }) => {
  switch (type) {
    case 'frontend':
      return (
        <svg xmlns="http://www.w3.org/2000/svg" className="layer-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      );
    case 'backend':
      return (
        <svg xmlns="http://www.w3.org/2000/svg" className="layer-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
        </svg>
      );
    case 'database':
      return (
        <svg xmlns="http://www.w3.org/2000/svg" className="layer-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
        </svg>
      );
    case 'devops':
      return (
        <svg xmlns="http://www.w3.org/2000/svg" className="layer-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
      );
    default:
      return null;
  }
};

export default function StackView({ project, recommendation }) {
  const [stack, setStack] = useState(recommendation || null);
  const [loading, setLoading] = useState(!recommendation);

  useEffect(() => {
    // Eğer prop gelirse state'i güncelle (ChatView'dan anlık güncellenme için)
    if (recommendation) {
      setStack(recommendation);
      setLoading(false);
      return;
    }

    async function loadStack() {
      if (!project?.id) return;
      setLoading(true);
      const data = await getLatestStack(project.id);
      setStack(data);
      setLoading(false);
    }
    loadStack();
  }, [project?.id, recommendation]);

  if (loading) {
    return (
      <div className="view-container stack-view glass flex items-center justify-center">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (!stack) {
    return (
      <div className="view-container stack-view glass">
        <div className="view-header">
          <h2>{project?.project_name || 'No Project Selected'} - Stack</h2>
          <p className="subtitle">Önerilen teknoloji yığını burada görünecek.</p>
        </div>
        <div className="empty-state">
          <p>Henüz bir stack önerisi oluşturulmamış. Sohbet ederek projenizi şekillendirin!</p>
        </div>
      </div>
    );
  }

  const layers = [
    { id: 'frontend', title: 'Frontend', content: stack.frontend_content, color: 'blue' },
    { id: 'backend', title: 'Backend', content: stack.backend_content, color: 'purple' },
    { id: 'database', title: 'Veritabanı', content: stack.database_content, color: 'indigo' },
    { id: 'devops', title: 'DevOps & Bulut', content: stack.devops_content, color: 'emerald' },
  ];

  return (
    <div className="view-container stack-view glass">
      <div className="view-header">
        <div className="header-badge">Sürüm v{stack.version}</div>
        <h2>{project?.project_name} - Teknoloji Yığını</h2>
        <p className="subtitle">Proje gereksinimlerinize göre optimize edilmiş akademik mimari önerisi.</p>
      </div>

      <div className="stack-grid">
        {layers.map((layer) => (
          <div key={layer.id} className={`stack-card-premium ${layer.color} glass`}>
            <div className="card-top">
              <div className={`icon-wrapper ${layer.color}`}>
                <LayerIcon type={layer.id} />
              </div>
              <h3>{layer.title}</h3>
            </div>
            <div className="card-body">
              {layer.content ? (
                <div className="content-text">{layer.content}</div>
              ) : (
                <div className="content-placeholder">Henüz seçim yapılmadı.</div>
              )}
            </div>
            <div className="card-footer">
              <span className="status-dot"></span>
              <span>Aktif Öneri</span>
            </div>
          </div>
        ))}
      </div>
      
      <div className="stack-info-footer">
        <p>Bu öneriler, Developlus Bilgi Tabanı ve akademik RAG mimarisi tarafından sentezlenmiştir.</p>
        <span className="timestamp">Son Güncelleme: {new Date(stack.created_at).toLocaleString('tr-TR')}</span>
      </div>
    </div>
  );
}
