const parser = require('lambda-multipart-parser');
const FormData = require('form-data');

exports.handler = async function (event, context) {
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      body: JSON.stringify({ error: 'Method not allowed' }),
    };
  }

  const apiKey = process.env.SARVAM_API_KEY || '';

  if (!apiKey || apiKey === 'your_sarvam_api_key_here') {
    return {
      statusCode: 400,
      body: JSON.stringify({
        error: 'SARVAM_API_KEY is not configured in Netlify environment variables.',
      }),
    };
  }

  try {
    // Parse the multipart form-data request
    const parsed = await parser.parse(event);
    const file = parsed.files && parsed.files[0];

    if (!file) {
      return {
        statusCode: 400,
        body: JSON.stringify({ error: 'No audio file received.' }),
      };
    }

    // Reconstruct the form-data request exactly as required by the Sarvam API
    const formData = new FormData();
    formData.append('file', file.content, {
      filename: file.filename || 'recording.wav',
      contentType: file.contentType || 'audio/wav',
    });
    formData.append('model', 'saaras:v3');
    formData.append('mode', 'transcribe');

    const startTime = Date.now();

    const sarvamResponse = await fetch('https://api.sarvam.ai/speech-to-text', {
      method: 'POST',
      headers: {
        'api-subscription-key': apiKey,
        ...formData.getHeaders(),
      },
      body: formData,
    });

    const sttLatencyMs = Date.now() - startTime;

    if (!sarvamResponse.ok) {
      const errorBody = await sarvamResponse.text();
      console.error(`[Sarvam STT Error ${sarvamResponse.status}]:`, errorBody);
      return {
        statusCode: sarvamResponse.status,
        body: JSON.stringify({
          error: `Sarvam STT API Error (${sarvamResponse.status}): ${errorBody || sarvamResponse.statusText}`,
        }),
      };
    }

    const data = await sarvamResponse.json();

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        success: true,
        transcript: data.transcript || '',
        confidence: 0.98,
        sttLatency: sttLatencyMs,
        languageCode: data.language_code || 'en-IN',
      }),
    };
  } catch (err) {
    console.error('STT proxy error:', err);
    return {
      statusCode: 500,
      body: JSON.stringify({
        error: `STT Backend Error: ${err.message}`,
      }),
    };
  }
};
