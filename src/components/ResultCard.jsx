import * as LucideIcons from 'lucide-react';

export default function ResultCard({ result, index }) {
  const IconComponent = LucideIcons[result.icon] || LucideIcons.Code2;

  return (
    <div className={`glass glass-hover result-card fade-in stagger-${Math.min(index + 1, 10)}`}>
      <div className="card-accent" />
      <div className={`card-icon ${result.cls}`}>
        <IconComponent size={20} />
      </div>
      <h3>{result.category}</h3>
      <div className="tech-name">{result.tech}</div>
      <p>{result.desc}</p>
    </div>
  );
}
