import React, { useState } from 'react';
import { Sparkles, FileText, Check, Copy, ExternalLink, Bookmark, AlertTriangle } from 'lucide-react';

export default function AnswerCard({ answer, sources, timestamp, isProcessing, status, reason }) {
  const [copied, setCopied] = useState(false);
  const isRefused = status === 'refused';

  if (!answer && !isProcessing) return null;

  const handleCopy = () => {
    if (!answer) return;
    navigator.clipboard.writeText(answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Convert basic markdown tags to styled JSX elements
  const renderMarkdown = (text) => {
    if (!text) return null;

    const lines = text.split('\n');
    return lines.map((line, idx) => {
      if (line.startsWith('### ')) {
        return <h3 key={idx}>{line.replace('### ', '')}</h3>;
      }
      if (line.startsWith('* ') || line.startsWith('- ')) {
        return (
          <ul key={idx}>
            <li>{renderInlineFormatting(line.substring(2))}</li>
          </ul>
        );
      }
      if (line.startsWith('> ')) {
        return (
          <blockquote key={idx}>
            {renderInlineFormatting(line.replace('> ', ''))}
          </blockquote>
        );
      }
      if (line.trim() === '') {
        return <div key={idx} style={{ height: '0.5rem' }}></div>;
      }
      return <p key={idx}>{renderInlineFormatting(line)}</p>;
    });
  };

  const renderInlineFormatting = (str) => {
    // Replace **bold** with <strong>
    const parts = str.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  return (
    <div className="glass-card answer-card">
      <div className="card-label">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--accent-purple)' }}>
          <Sparkles size={16} />
          <span>Grounded RAG Response</span>
          {timestamp && <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>• {timestamp}</span>}
        </div>
        
        {answer && (
          <button
            onClick={handleCopy}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.3rem',
              fontSize: '0.78rem',
            }}
          >
            {copied ? <Check size={14} color="var(--accent-emerald)" /> : <Copy size={14} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        )}
      </div>

      {/* Answer Body */}
      {isProcessing && !answer ? (
        <div style={{ padding: '1rem 0', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div style={{ height: '14px', background: 'rgba(255,255,255,0.06)', borderRadius: '4px', width: '70%' }}></div>
          <div style={{ height: '14px', background: 'rgba(255,255,255,0.04)', borderRadius: '4px', width: '90%' }}></div>
          <div style={{ height: '14px', background: 'rgba(255,255,255,0.04)', borderRadius: '4px', width: '60%' }}></div>
        </div>
      ) : isRefused ? (
        <div style={{
          padding: '1rem',
          background: 'rgba(245, 158, 11, 0.08)',
          border: '1px solid rgba(245, 158, 11, 0.25)',
          borderRadius: '8px',
          margin: '0.5rem 0',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: '#f59e0b', fontWeight: 600 }}>
            <AlertTriangle size={18} />
            <span>Not Enough Information</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', margin: 0, lineHeight: 1.6 }}>
            {answer}
          </p>
          {reason && (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.78rem', marginTop: '0.5rem', marginBottom: 0 }}>
              Reason: {reason.replace(/_/g, ' ')}
            </p>
          )}
        </div>
      ) : (
        <div className="markdown-body">
          {renderMarkdown(answer)}
        </div>
      )}

      {/* Source Citation Cards */}
      {sources && sources.length > 0 && (
        <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '1rem' }}>
          <div className="sources-header">
            <Bookmark size={12} style={{ display: 'inline', marginRight: '4px' }} />
            Retrieved Document Sources ({sources.length})
          </div>
          <div className="sources-grid" style={{ marginTop: '0.6rem' }}>
            {sources.map((src) => (
              <div key={src.id} className="source-item">
                <div className="source-title-row">
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <FileText size={13} />
                    {src.title}
                  </span>
                  <span style={{ fontSize: '0.72rem', color: 'var(--accent-emerald)', fontFamily: 'var(--font-mono)' }}>
                    {(src.score * 100).toFixed(0)}% Match
                  </span>
                </div>
                <div className="source-snippet">"{src.snippet}"</div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  Location: {src.page}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
