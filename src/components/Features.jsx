import { Zap, Brain, Code2, Layers } from 'lucide-react';

const features = [
  {
    icon: <Zap size={22} />,
    title: 'Hızlı Analiz',
    desc: 'Saniyeler içinde proje fikrini yapay zeka ile analiz et ve sonuçları gör.'
  },
  {
    icon: <Brain size={22} />,
    title: 'Akıllı Öneriler',
    desc: 'Proje gereksinimlerine göre en uygun teknolojileri otomatik belirle.'
  },
  {
    icon: <Code2 size={22} />,
    title: 'Geliştirici Dostu',
    desc: 'Temiz çıktılar, modern mimari önerileri ve doğrudan uygulanabilir sonuçlar.'
  },
  {
    icon: <Layers size={22} />,
    title: 'Modern Mimari',
    desc: 'Microservice, serverless ve monolith arasında projeye en uygun yaklaşımı öner.'
  }
];

export default function Features() {
  return (
    <section className="features-section" id="features">
      <div className="section-inner">
        <h2 className="section-title">Özellikler</h2>
        <p className="section-subtitle">Geliştiriciler için tasarlandı</p>
        <div className="features-grid">
          {features.map((f, i) => (
            <div key={f.title} className={`glass glass-hover feature-card fade-in stagger-${i + 1}`}>
              <div className="feat-icon">{f.icon}</div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
