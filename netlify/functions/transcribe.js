/**
 * Netlify Serverless Function: Sarvam STT Proxy
 * Matches exports.handler pattern for Netlify runtime.
 */

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
    // Netlify functions receive body as string/base64
    const rawBody = event.isBase64Encoded
      ? Buffer.from(event.body, 'base64')
      : Buffer.from(event.body);

    const contentType = event.headers['content-type'] || '';

    // Parse the incoming multipart form data using the Web API Request object
    const incomingRequest = new Request('http://localhost', {
      method: 'POST',
      headers: { 'Content-Type': contentType },
      body: rawBody,
    });
    const incomingForm = await incomingRequest.formData();

    // Extract the uploaded audio file
    const audioFile = incomingForm.get('file');
    if (!audioFile) {
      return {
        statusCode: 400,
        body: JSON.stringify({ error: 'No audio file received.' }),
      };
    }

    // Rebuild FormData with all fields required by the Sarvam API
    const sarvamForm = new FormData();
    sarvamForm.append('file', audioFile, audioFile.name || 'recording.wav');
    sarvamForm.append('model', incomingForm.get('model') || 'saaras:v3');
    sarvamForm.append('mode', incomingForm.get('mode') || 'transcribe');

    const startTime = Date.now();

    const sarvamResponse = await fetch('https://api.sarvam.ai/speech-to-text', {
      method: 'POST',
      headers: {
        'api-subscription-key': apiKey,
      },
      body: sarvamForm,
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
