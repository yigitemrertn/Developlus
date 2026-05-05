import React, { useState, useEffect } from 'react';
import { Key, Save, Check } from 'lucide-react';

export default function SettingsView() {
  const [apiKey, setApiKey] = useState('');
  const [isSaved, setIsSaved] = useState(false);

  useEffect(() => {
    const savedKey = localStorage.getItem('hf_api_key');
    if (savedKey) {
      setApiKey(savedKey);
    }
  }, []);

  const handleSave = () => {
    localStorage.setItem('hf_api_key', apiKey);
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 3000);
  };

  return (
    <div className="view-container settings-view glass">
      <div className="view-header">
        <h2>Settings</h2>
        <p className="subtitle">Configure application settings and API keys</p>
      </div>

      <div className="settings-content">
        <div className="settings-card glass">
          <h3>API Configuration</h3>
          <p className="settings-desc">
            Enter your HuggingFace API key to enable AI-powered tech stack recommendations and chat.
          </p>
          
          <div className="input-group">
            <label>HuggingFace API Key</label>
            <div className="input-wrapper">
              <Key size={18} className="input-icon" />
              <input 
                type="password" 
                placeholder="hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" 
                value={apiKey}
                onChange={(e) => {
                  setApiKey(e.target.value);
                  setIsSaved(false);
                }}
              />
            </div>
          </div>

          <button 
            className={`survey-nav-btn ${isSaved ? 'secondary' : 'primary'}`} 
            onClick={handleSave}
            style={{ marginTop: '20px' }}
          >
            {isSaved ? (
              <><Check size={18} /> Saved successfully</>
            ) : (
              <><Save size={18} /> Save Settings</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
