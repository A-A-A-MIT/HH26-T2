import React, { useState, useEffect } from 'react';
import { Mic, Zap, ShieldCheck } from 'lucide-react';

export default function Header() {
  const [apiKeyConfigured, setApiKeyConfigured] = useState(false);

  useEffect(() => {
    // Check backend health & key status
    fetch('/api/health')
      .then((res) => res.json())
      .then((data) => {
        setApiKeyConfigured(data.sarvamApiKeyConfigured);
      })
      .catch(() => {
        setApiKeyConfigured(false);
      });
  }, []);

  return (
    <header className="glass-card header-bar">
      <div className="brand-section">
        <div className="brand-icon">
          <Mic size={22} />
        </div>
        <div>
          <div className="brand-title">HH Goa 2026 — Task 2</div>
          <div className="brand-subtitle">Sarvam Speech-to-Text & Voice RAG</div>
        </div>
      </div>

      <div className="header-badges">
        <span
          className="badge"
          style={{
            background: apiKeyConfigured ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
            color: apiKeyConfigured ? 'var(--accent-emerald)' : 'var(--accent-amber)',
            borderColor: apiKeyConfigured ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)',
          }}
        >
          <Zap size={13} />
          {apiKeyConfigured ? 'SARVAM STT READY' : 'PASTE API KEY IN .ENV'}
        </span>
        <span className="badge badge-status">
          <ShieldCheck size={13} />
          SECURE SERVER PROXY
        </span>
      </div>
    </header>
  );
}
