import { describe, expect, it } from 'vitest';
import worker, { SECURITY_HEADERS, type Env } from '../src/worker';

const env: Env = {
  ASSETS: {
    fetch: async (request: Request) => {
      const { pathname } = new URL(request.url);
      if (pathname === '/missing') return new Response('Not found', { status: 404 });
      return new Response(`asset ${pathname}`, { headers: { 'Content-Type': 'text/html' } });
    },
  },
};

const get = (path: string) => worker.fetch(new Request(`https://trkr.example${path}`), env);

describe('worker', () => {
  it('serves assets with the security headers', async () => {
    const response = await get('/');
    expect(await response.text()).toBe('asset /');
    for (const [name, value] of Object.entries(SECURITY_HEADERS)) {
      expect(response.headers.get(name)).toBe(value);
    }
    expect(response.headers.get('Content-Security-Policy')).toContain("connect-src 'self'");
  });

  it('caches hashed assets for good, and nothing else', async () => {
    expect((await get('/assets/index-abc123.js')).headers.get('Cache-Control')).toContain('immutable');
    expect((await get('/')).headers.get('Cache-Control')).toBeNull();
  });

  it('keeps the status of a missing asset', async () => {
    const response = await get('/missing');
    expect(response.status).toBe(404);
    expect(response.headers.get('X-Frame-Options')).toBe('DENY');
  });

  it('answers the health check, and 404 on other API paths', async () => {
    const health = await get('/api/health');
    expect(await health.json()).toEqual({ ok: true, snapshot_schema_version: 1 });
    expect(health.headers.get('Cache-Control')).toBe('no-store');
    expect((await get('/api/snapshot')).status).toBe(404);
  });
});
