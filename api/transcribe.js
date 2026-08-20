/**
 * Vercel Serverless Function: Sarvam STT Proxy
 * Proxies audio blobs to Sarvam Speech-to-Text API.
 * SARVAM_API_KEY is stored in Vercel Environment Variables (never exposed to client).
 */

export const config = {
  api: {
    bodyParser: false, // We need raw body for multipart form data
  },
  regions: ['iad1'], // US East to match Cloud Run
};

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const apiKey = process.env.SARVAM_API_KEY || '';

  if (!apiKey || apiKey === 'your_sarvam_api_key_here') {
    return res.status(400).json({
      error: 'SARVAM_API_KEY is not configured in Vercel Environment Variables.',
    });
  }

  try {
    // Collect the raw request body
    const chunks = [];
    for await (const chunk of req) {
      chunks.push(chunk);
    }
    const body = Buffer.concat(chunks);

    // Extract content-type header to preserve multipart boundary
    const contentType = req.headers['content-type'] || '';

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
      return res.status(sarvamResponse.status).json({
        error: `Sarvam STT API Error (${sarvamResponse.status}): ${errorBody || sarvamResponse.statusText}`,
      });
    }

    const data = await sarvamResponse.json();

    return res.status(200).json({
      success: true,
      transcript: data.transcript || '',
      confidence: 0.98,
      sttLatency: sttLatencyMs,
      languageCode: data.language_code || 'en-IN',
    });
  } catch (err) {
    console.error('STT proxy error:', err);
    return res.status(500).json({
      error: `STT Backend Error: ${err.message}`,
    });
  }
}
