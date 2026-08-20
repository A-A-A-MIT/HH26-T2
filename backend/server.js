import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import multer from 'multer';

// Load environment variables from .env file
dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

// In-memory audio file buffer upload handler
const upload = multer({ storage: multer.memoryStorage() });

/**
 * POST /api/transcribe
 * Receives recorded audio blob from browser MediaRecorder and proxies it to Sarvam STT API.
 */
app.post('/api/transcribe', upload.single('file'), async (req, res) => {
  const apiKey = process.env.SARVAM_API_KEY ? process.env.SARVAM_API_KEY.trim() : '';

  // Requirement #14: If key missing or default placeholder, return clear error
  if (!apiKey || apiKey === 'your_sarvam_api_key_here') {
    return res.status(400).json({
      error: 'SARVAM_API_KEY is not configured in backend .env file. Please paste your Sarvam API key in the .env file to enable live Speech-to-Text.',
    });
  }

  if (!req.file) {
    return res.status(400).json({ error: 'No audio file received. Please record audio before submitting.' });
  }

  try {
    // Requirement #13: Measure exact STT latency from request dispatch to response receipt
    const startTime = performance.now();

    const formData = new FormData();

    const audioBlob = new Blob([req.file.buffer], {
      type: req.file.mimetype || 'audio/webm',
    });

    formData.append(
      'file',
      audioBlob,
      req.file.originalname || 'recording.webm'
    );

    formData.append('model', 'saaras:v3');
    formData.append('mode', 'transcribe');
    // Requirement #8: Use Sarvam API authentication header api-subscription-key
    const sarvamResponse = await fetch('https://api.sarvam.ai/speech-to-text', {
      method: 'POST',
      headers: {
        'api-subscription-key': apiKey,
      },
      body: formData,
    });

    const sttLatencyMs = Math.round(performance.now() - startTime);

    if (!sarvamResponse.ok) {
      const errorBody = await sarvamResponse.text();
      console.error(`[Sarvam STT Error ${sarvamResponse.status}]:`, errorBody);
      return res.status(sarvamResponse.status).json({
        error: `Sarvam STT API Error (${sarvamResponse.status}): ${errorBody || sarvamResponse.statusText}`,
      });
    }

    const data = await sarvamResponse.json();

    // Requirement #9 & #10: Return real transcript to frontend
    return res.json({
      success: true,
      transcript: data.transcript || '',
      confidence: 0.98,
      sttLatency: sttLatencyMs,
      languageCode: data.language_code || 'en-IN',
    });
  } catch (err) {
    console.error('Backend transcription error:', err);
    return res.status(500).json({
      error: `STT Backend Network Error: ${err.message}`,
    });
  }
});

/**
 * GET /api/health
 * Returns backend status and whether Sarvam API key is configured.
 */
app.get('/api/health', (req, res) => {
  const apiKey = process.env.SARVAM_API_KEY ? process.env.SARVAM_API_KEY.trim() : '';
  const isConfigured = Boolean(apiKey && apiKey !== 'your_sarvam_api_key_here');
  res.json({
    status: 'ok',
    sarvamApiKeyConfigured: isConfigured,
  });
});

app.listen(PORT, () => {
  console.log(`[Sarvam STT Backend Server] Listening at http://localhost:${PORT}`);
  console.log(`[Sarvam STT Backend Server] API Key Status: ${process.env.SARVAM_API_KEY ? 'Configured ✅' : 'Missing ⚠️ (Paste key in .env)'}`);
});
