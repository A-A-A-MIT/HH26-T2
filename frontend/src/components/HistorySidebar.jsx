import React from 'react';
import { History, MessageSquare, Trash2, Clock, Sparkles } from 'lucide-react';

export default function HistorySidebar({ history, activeHistoryId, onSelectHistory, onClearHistory }) {
  if (!history || history.length === 0) {
    return (
      <div className="glass-card history-card">
        <div className="card-label">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--accent-purple)' }}>
            <History size={16} />
            <span>Chat History</span>
          </div>
        </div>
        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center', padding: '1.5rem 0' }}>
          No past voice queries yet. Submit a query to start building chat history!
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card history-card">
      <div className="card-label">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--accent-purple)' }}>
          <History size={16} />
          <span>Chat History ({history.length})</span>
        </div>
        <button
          onClick={onClearHistory}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.25rem',
            fontSize: '0.75rem',
          }}
          title="Clear history"
        >
          <Trash2 size={13} />
          <span>Clear</span>
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', overflowY: 'auto' }}>
        {history.map((item) => {
          const isActive = item.id === activeHistoryId;
          const totalMs = item.ragResult?.metrics?.totalLatencyMs || 0;
          return (
            <div
              key={item.id}
              className={`history-item ${isActive ? 'active' : ''}`}
              onClick={() => onSelectHistory(item)}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <MessageSquare size={13} color="var(--accent-purple)" />
                <span className="history-query">{item.query}</span>
              </div>
              <div className="history-meta">
                <span>{item.timestamp}</span>
                {totalMs > 0 && (
                  <span style={{ color: 'var(--accent-emerald)', fontFamily: 'var(--font-mono)' }}>
                    {Math.round(totalMs)} ms
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
