import { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import HowItWorks from './components/HowItWorks';
import Features from './components/Features';
import Dashboard from './components/Dashboard';
import ChatPanel from './components/ChatPanel';
import Footer from './components/Footer';
import { analyzeProject } from './api/analyzeApi';

export default function App() {
  const [page, setPage] = useState('landing'); // 'landing' | 'dashboard'
  const [results, setResults] = useState([]);
  const [prompt, setPrompt] = useState('');

  // Scroll to top on page change
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [page]);

  async function handleAnalyze(input) {
    setPrompt(input);
    const data = await analyzeProject(input);
    setResults(data);
    setPage('dashboard');
  }

  function handleBack() {
    setPage('landing');
  }

  return (
    <div className="app-root" id="appRoot">
      <div className="noise-overlay" />
      <div className="glow-orb glow-2" />

      <Navbar onHomeClick={handleBack} />

      {page === 'landing' && (
        <>
          <Hero onAnalyze={handleAnalyze} />
          <HowItWorks />
          <Features />
          <Footer />
        </>
      )}

      {page === 'dashboard' && (
        <Dashboard
          results={results}
          prompt={prompt}
          onBack={handleBack}
        />
      )}

      <ChatPanel />
    </div>
  );
}
