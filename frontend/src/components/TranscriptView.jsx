import React from 'react';
import { Mic, CheckCircle2, Clock } from 'lucide-react';

export default function TranscriptView({ transcript, confidence, audioDuration, sttLatency }) {
  if (!transcript) return null;

  return (
    <div className="glass-card transcript-card">
      <div className="card-label">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--accent-cyan)' }}>
          <Mic size={14} />
          <span>Speech-to-Text Transcript</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          {confidence && (
            <span className="badge" style={{ background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-emerald)' }}>
              <CheckCircle2 size={12} />
              {(confidence * 100).toFixed(0)}% Match
            </span>
          )}
          {sttLatency > 0 && (
            <span className="badge" style={{ background: 'rgba(139, 92, 246, 0.15)', color: 'var(--accent-purple)' }}>
              <Clock size={12} />
              {sttLatency} ms STT
            </span>
          )}
        </div>
      </div>

      <div className="transcript-text">
        "{transcript}"
      </div>
    </div>
  );
}
