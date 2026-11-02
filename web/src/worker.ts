// The Cloudflare Worker: serves the built page from dist/ and adds the security headers.
// It stores nothing and receives no portfolio data: snapshots are opened in the browser.

import { SCHEMA_VERSION } from './snapshot';

export interface Env {
  ASSETS: { fetch(request: Request): Promise<Response> };
}

// The page may only load its own files and talk to its own origin, so a snapshot opened in
// it can't be sent anywhere else, and no third-party script can run in it.
export const SECURITY_HEADERS: Record<string, string> = {
  'Content-Security-Policy': [
    "default-src 'none'",
    "script-src 'self'",
    "style-src 'self'",
    "img-src 'self' data:",
    "connect-src 'self'",
    "manifest-src 'self'",
    "base-uri 'none'",
    "form-action 'none'",
    "frame-ancestors 'none'",
  ].join('; '),
  'Cross-Origin-Opener-Policy': 'same-origin',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=(), usb=()',
  'Referrer-Policy': 'no-referrer',
  'Strict-Transport-Security': 'max-age=31536000',
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  // A personal tool: keep it out of search results.
  'X-Robots-Tag': 'noindex, nofollow',
};

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const { pathname } = new URL(request.url);
    let response: Response;
    if (pathname === '/api/health') {
      response = Response.json({ ok: true, snapshot_schema_version: SCHEMA_VERSION });
    } else if (pathname.startsWith('/api/')) {
      response = Response.json({ error: 'Not found.' }, { status: 404 });
    } else {
      response = await env.ASSETS.fetch(request);
    }
    return secured(response, pathname);
  },
};

function secured(response: Response, pathname: string): Response {
  const result = new Response(response.body, response);
  for (const [name, value] of Object.entries(SECURITY_HEADERS)) result.headers.set(name, value);
  if (pathname.startsWith('/api/')) {
    result.headers.set('Cache-Control', 'no-store');
  } else if (pathname.startsWith('/assets/') && response.ok) {
    // Vite puts a content hash in these names, so a changed file gets a new name.
    result.headers.set('Cache-Control', 'public, max-age=31536000, immutable');
  }
  return result;
}
