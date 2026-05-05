import React from 'react';

export default function StackView({ project, recommendations }) {
  const stack = recommendations || { frontend: '', backend: '', database: '', devops: '' };

  const quadrants = [
    { id: 'frontend', title: 'A. Frontend (Client-Side)', desc: 'Kullanıcının gördüğü ve etkileşime girdiği kısım.', content: stack.frontend },
    { id: 'backend', title: 'B. Backend (Server-Side)', desc: 'İş mantığının (business logic) döndüğü, verilerin işlendiği mutfak.', content: stack.backend },
    { id: 'database', title: 'C. Database (Storage)', desc: 'Verinin nerede ve nasıl saklanacağı.', content: stack.database },
    { id: 'devops', title: 'D. Infrastructure & DevOps', desc: 'Uygulamanın nerede yaşayacağı ve nasıl yayılacağı.', content: stack.devops },
  ];

  return (
    <div className="view-container stack-view glass">
       <div className="view-header">
        <h2>{project?.name || 'Proje Seçilmedi'} - Stack Görünümü</h2>
        <p className="subtitle">Önerilen teknoloji yığını bileşenleri</p>
      </div>

      <div className="stack-grid">
        {quadrants.map(q => (
          <div key={q.id} className="stack-card glass">
            <div className="stack-card-header">
              <h3>{q.title}</h3>
              <p>{q.desc}</p>
            </div>
            <div className="stack-card-content rich-text-box">
              {q.content ? (
                q.content.split('\n').map((line, i) => (
                  <span key={i}>{line}<br/></span>
                ))
              ) : (
                <div className="empty-stack-content">
                  Henüz bu kategori için bir öneri bulunmuyor. Chat görünümünden projeyi detaylandırmasını isteyebilirsiniz.
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
