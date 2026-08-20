import React, { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, Send, Sparkles, AlertCircle } from 'lucide-react';
import { DEMO_PRESETS } from '../services/api';

export default function InputPanel({
  queryText,
  setQueryText,
  onStartRecord,
  onStopRecord,
  isRecording,
  onSubmit,
  isProcessing,
  pipelinePhase,
  error,
}) {
  const [recordTimer, setRecordTimer] = useState(0);
  const timerRef = useRef(null);

  // Manage live recording timer
  useEffect(() => {
    if (isRecording) {
      setRecordTimer(0);
      timerRef.current = setInterval(() => {
        setRecordTimer((prev) => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isRecording]);

  const formatTimer = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <div className="glass-card input-card">
      {/* Preset Quick Chips */}
      <div>
        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
          TRY PRESET DEMO QUERIES:
        </div>
        <div className="presets-container">
          {DEMO_PRESETS.map((preset) => (
            <button
              key={preset.id}
              className="preset-chip"
              onClick={() => setQueryText(preset.query)}
              disabled={isProcessing || isRecording}
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Text Input Area */}
      <div className="input-area-wrapper">
        <textarea
          className="prompt-textarea"
          placeholder="Ask a question about HH Goa Task 2, Sarvam AI, or low-latency RAG architectures... (or click the microphone to speak)"
          value={queryText}
          onChange={(e) => setQueryText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isRecording || isProcessing}
        />
      </div>

      {/* Error Banner */}
      {error && (
        <div className="error-banner">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Input Action Controls */}
      <div className="input-actions-bar">
        {/* Mic Control */}
        <div className="mic-control-wrapper">
          <button
            type="button"
            className={`btn-mic ${isRecording ? 'recording' : ''}`}
            onClick={isRecording ? onStopRecord : onStartRecord}
            disabled={isProcessing}
            title={isRecording ? 'Click to stop recording' : 'Click to record voice prompt'}
          >
            {isRecording ? <MicOff size={24} /> : <Mic size={24} />}
          </button>

          {isRecording ? (
            <div className="recording-indicator">
              <span className="recording-time">REC {formatTimer(recordTimer)}</span>
              <div className="waveform-anim">
                <span className="wave-bar"></span>
                <span className="wave-bar"></span>
                <span className="wave-bar"></span>
                <span className="wave-bar"></span>
                <span className="wave-bar"></span>
              </div>
            </div>
          ) : (
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              {isProcessing ? 'Processing pipeline...' : 'Click mic to speak'}
            </span>
          )}
        </div>

        {/* Submit Button */}
        <button
          type="button"
          className="btn-submit"
          onClick={onSubmit}
          disabled={isProcessing || isRecording || !queryText.trim()}
        >
          {isProcessing ? (
            <>
              <span className="spinner"></span>
              <span>{pipelinePhase || 'Processing...'}</span>
            </>
          ) : (
            <>
              <Sparkles size={16} />
              <span>Ask Assistant</span>
              <Send size={14} />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
