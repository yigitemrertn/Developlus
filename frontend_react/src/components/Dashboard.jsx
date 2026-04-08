import { ArrowLeft } from 'lucide-react';
import ResultCard from './ResultCard';

export default function Dashboard({ results, prompt, onBack }) {
  const shortPrompt = prompt.length > 60
    ? prompt.substring(0, 60) + '...'
    : prompt;

  return (
    <div className="dashboard-section">
      <div className="section-inner" style={{ paddingTop: '40px', paddingBottom: '60px' }}>
        <button className="back-btn" onClick={onBack}>
          <ArrowLeft size={16} />
          Geri Dön
        </button>

        <div className="results-header">
          <h2>Analiz Sonuçları</h2>
          <p>"{shortPrompt}" projesi için önerilen teknoloji yığını</p>
        </div>

        <div className="results-grid">
          {results.map((result, i) => (
            <ResultCard key={result.category} result={result} index={i} />
          ))}
        </div>
      </div>
    </div>
  );
}
