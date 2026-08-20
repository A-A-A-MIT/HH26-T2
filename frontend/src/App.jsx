import React, { useState, useRef } from 'react';
import Header from './components/Header';
import InputPanel from './components/InputPanel';
import TranscriptView from './components/TranscriptView';
import AnswerCard from './components/AnswerCard';
import MetricsDashboard from './components/MetricsDashboard';
import HistorySidebar from './components/HistorySidebar';
import { transcribeAudio, processQuery } from './services/api';

export default function App() {
  const [queryText, setQueryText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [pipelinePhase, setPipelinePhase] = useState(''); // 'transcribing' | 'retrieving' | 'generating'
  const [error, setError] = useState(null);

  // Chat History State
  const [history, setHistory] = useState([]);
  const [activeHistoryId, setActiveHistoryId] = useState(null);

  // STT Output State
  const [sttResult, setSttResult] = useState({
    transcript: '',
    confidence: null,
    audioDuration: null,
    sttLatency: 0,
  });

  // RAG Output State
  const [ragResult, setRagResult] = useState({
    answer: '',
    sources: [],
    metrics: null,
    timestamp: '',
  });

  // Browser MediaRecorder Refs
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Start Voice Recording via native MediaRecorder API
  const handleStartRecord = async () => {
    setError(null);
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Microphone access is not supported in this browser environment.');
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];

      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm';

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());

        const audioBlob = new Blob(audioChunksRef.current, {
          type: mimeType,
        });

        if (audioBlob.size === 0) {
          setError('Recording is empty — no audio was captured.');
          return;
        }

        await handleAudioProcess(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.warn('Microphone error:', err);
      setError('Microphone permission denied or device not found. Please allow microphone access in your browser settings.');
      setIsRecording(false);
    }
  };

  // Stop Recording and trigger STT Pipeline
  const handleStopRecord = () => {
    setIsRecording(false);
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    } else {
      handleAudioProcess(null);
    }
  };

  // Execute STT + RAG workflow for audio inputs (with live token streaming)
  const handleAudioProcess = async (audioBlob) => {
    setIsProcessing(true);
    setPipelinePhase('transcribing');
    setError(null);
    setRagResult({ answer: '', sources: [], metrics: null, timestamp: '' });

    try {
      const sttResponse = await transcribeAudio(audioBlob);
      const newStt = {
        transcript: sttResponse.transcript,
        confidence: sttResponse.confidence,
        audioDuration: sttResponse.audioDuration,
        sttLatency: sttResponse.sttLatency,
      };
      setSttResult(newStt);
      setQueryText(sttResponse.transcript);

      const ragData = await processQuery(
        sttResponse.transcript,
        sttResponse.sttLatency,
        (phase) => setPipelinePhase(phase)
      );

      const finalRag = {
        answer: ragData.answer,
        sources: ragData.sources,
        metrics: ragData.metrics,
        timestamp: ragData.timestamp,
        status: ragData.status,
        reason: ragData.reason,
      };
      setRagResult(finalRag);

      // Save turn into Chat History
      const historyItem = {
        id: Date.now().toString(),
        timestamp: ragData.timestamp,
        query: sttResponse.transcript,
        sttResult: newStt,
        ragResult: finalRag,
      };
      setHistory((prev) => [historyItem, ...prev]);
      setActiveHistoryId(historyItem.id);
    } catch (err) {
      setError(err.message || 'An error occurred during audio processing.');
    } finally {
      setIsProcessing(false);
      setPipelinePhase('');
    }
  };

  // Execute RAG workflow for direct text submission (with live token streaming)
  const handleSubmitQuery = async () => {
    if (!queryText.trim() || isProcessing) return;

    const currentQuery = queryText.trim();
    setIsProcessing(true);
    setError(null);
    setPipelinePhase('retrieving');
    setRagResult({ answer: '', sources: [], metrics: null, timestamp: '' });
    const emptyStt = { transcript: '', confidence: null, audioDuration: null, sttLatency: 0 };
    setSttResult(emptyStt);

    try {
      const ragData = await processQuery(
        currentQuery,
        0,
        (phase) => setPipelinePhase(phase)
      );

      const finalRag = {
        answer: ragData.answer,
        sources: ragData.sources,
        metrics: ragData.metrics,
        timestamp: ragData.timestamp,
        status: ragData.status,
        reason: ragData.reason,
      };
      setRagResult(finalRag);

      // Save turn into Chat History
      const historyItem = {
        id: Date.now().toString(),
        timestamp: ragData.timestamp,
        query: currentQuery,
        sttResult: emptyStt,
        ragResult: finalRag,
      };
      setHistory((prev) => [historyItem, ...prev]);
      setActiveHistoryId(historyItem.id);
    } catch (err) {
      setError(err.message || 'An error occurred while synthesizing the response.');
    } finally {
      setIsProcessing(false);
      setPipelinePhase('');
    }
  };

  const handleSelectHistory = (item) => {
    setActiveHistoryId(item.id);
    setQueryText(item.query);
    if (item.sttResult) setSttResult(item.sttResult);
    if (item.ragResult) setRagResult(item.ragResult);
  };

  const handleClearHistory = () => {
    setHistory([]);
    setActiveHistoryId(null);
  };

  return (
    <div className="app-layout">
      {/* Header Banner */}
      <Header />

      {/* Main Content 3-Column Grid */}
      <div className="main-grid">
        {/* Left Column: Chat History Sidebar */}
        <div className="history-sidebar-container">
          <HistorySidebar
            history={history}
            activeHistoryId={activeHistoryId}
            onSelectHistory={handleSelectHistory}
            onClearHistory={handleClearHistory}
          />
        </div>

        {/* Center Column: Input Panel, Transcript & Answer */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Query & Mic Controls */}
          <InputPanel
            queryText={queryText}
            setQueryText={setQueryText}
            onStartRecord={handleStartRecord}
            onStopRecord={handleStopRecord}
            isRecording={isRecording}
            onSubmit={handleSubmitQuery}
            isProcessing={isProcessing}
            pipelinePhase={pipelinePhase}
            error={error}
          />

          {/* STT Transcript Display */}
          <TranscriptView
            transcript={sttResult.transcript}
            confidence={sttResult.confidence}
            audioDuration={sttResult.audioDuration}
            sttLatency={sttResult.sttLatency}
          />

          {/* RAG Answer Display */}
          <AnswerCard
            answer={ragResult.answer}
            sources={ragResult.sources}
            timestamp={ragResult.timestamp}
            isProcessing={isProcessing}
            status={ragResult.status}
            reason={ragResult.reason}
          />
        </div>

        {/* Right Column: Latency & Metrics Dashboard */}
        <MetricsDashboard
          metrics={ragResult.metrics}
          isProcessing={isProcessing}
          pipelinePhase={pipelinePhase}
        />
      </div>
    </div>
  );
}
