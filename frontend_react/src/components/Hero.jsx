import { useState } from 'react';
import { Sparkles } from 'lucide-react';

export default function Hero({ onAnalyze }) {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleAnalyze() {
    if (!input.trim()) return;
    setLoading(true);
    await onAnalyze(input.trim());
    setLoading(false);
  }

  function handleKey(e) {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleAnalyze();
  }

  return (
    <section className="hero" id="hero">
      <div className="section-inner" style={{ position: 'relative' }}>
        <div className="glow-orb glow-1" />
        <div className="glow-orb glow-3" />

        <h1>
          Projen için doğru teknolojileri{' '}
          <span className="gradient-text">saniyeler içinde</span>{' '}
          keşfet
        </h1>

        <p>
          Developlus, proje fikrini analiz eder ve sana frontend, backend,
          veritabanı, mimari ve diğer teknik gereksinimler için akıllı öneriler sunar.
        </p>

        <div className="input-area">
          <textarea
            id="projectInput"
            placeholder="Proje fikrini buraya yaz... Örn: E-ticaret platformu, gerçek zamanlı chat uygulaması, SaaS dashboard..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
          />
          <button
            className="analyze-btn"
            id="analyzeBtn"
            onClick={handleAnalyze}
            disabled={loading || !input.trim()}
          >
            {loading ? (
              <span className="btn-loader">
                <div className="spinner" />
                Analiz ediliyor...
              </span>
            ) : (
              <>
                <Sparkles size={18} />
                Analiz Et
              </>
            )}
          </button>
          <p style={{ color: '#6b7280', fontSize: '12px', marginTop: '8px' }}>
            Ctrl + Enter ile de gönderebilirsin
          </p>
        </div>
      </div>
    </section>
  );
}
