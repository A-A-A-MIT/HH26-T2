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
    const body = event.isBase64Encoded
      ? Buffer.from(event.body, 'base64')
      : Buffer.from(event.body);

    const contentType = event.headers['content-type'] || '';

    const startTime = Date.now();

    const sarvamResponse = await fetch('https://api.sarvam.ai/speech-to-text', {
      method: 'POST',
      headers: {
        'api-subscription-key': apiKey,
        'Content-Type': contentType,
      },
      body: body,
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
