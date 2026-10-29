import { redirect } from 'next/navigation';
import { getServerSession } from 'next-auth';

import { authOptions } from '@/lib/auth';

type ServiceHealth = {
  url: string;
  status: 'up' | 'down';
  status_code: number | null;
  response_time_ms: number;
  error?: string;
};

type HealthResponse = {
  status: 'ok' | 'degraded';
  down_services: string[];
  services: Record<string, ServiceHealth>;
};

const portalLinks = [
  { key: 'outline', title: 'Outline', url: 'http://localhost:3000', tag: 'knowledge' },
  { key: 'frontend', title: 'Portal Frontend', url: 'http://localhost:3005', tag: 'home' },
  { key: 'backend', title: 'FastAPI Docs', url: 'http://localhost:8000/docs', tag: 'api' },
  { key: 'keycloak', title: 'Keycloak', url: 'http://localhost:8080', tag: 'auth' },
  { key: 'vikunja', title: 'Vikunja', url: 'http://localhost:3456', tag: 'tasks' },
  { key: 'n8n', title: 'n8n', url: 'http://localhost:5678', tag: 'automation' },
  { key: 'open_webui', title: 'Open WebUI', url: 'http://localhost:3002', tag: 'ai' },
  { key: 'meilisearch', title: 'Meilisearch', url: 'http://localhost:7700', tag: 'search' },
  { key: 'appsmith', title: 'Appsmith', url: 'http://localhost:8085', tag: 'apps' },
  { key: 'gotify', title: 'Gotify', url: 'http://localhost:8086', tag: 'notify' },
  { key: 'stirling_pdf', title: 'Stirling PDF', url: 'http://localhost:8087', tag: 'documents' },
  { key: 'nocodb', title: 'NocoDB', url: 'http://localhost:8088', tag: 'data' },
];

async function fetchHealth(): Promise<HealthResponse | null> {
  const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://backend:8000';
  try {
    const response = await fetch(`${apiBase}/api/services/health`, {
      cache: 'no-store',
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as HealthResponse;
  } catch {
    return null;
  }
}

export default async function Home() {
  const authEnabled = process.env.FRONTEND_AUTH_ENABLED === 'true';
  const session = await getServerSession(authOptions);

  if (authEnabled && !session) {
    redirect('/api/auth/signin?callbackUrl=/');
  }

  const health = await fetchHealth();

  return (
    <main
      style={{
        minHeight: '100vh',
        margin: 0,
        padding: '2.2rem 1.2rem 3rem',
        color: '#19202a',
        background:
          'radial-gradient(circle at 15% 15%, #f9f4ea 0%, #f4eee1 30%, #e9edf2 70%, #dee7f1 100%)',
        fontFamily: 'ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif',
      }}
    >
      <section
        style={{
          maxWidth: 1100,
          margin: '0 auto',
          background: 'rgba(255,255,255,0.72)',
          border: '1px solid rgba(25,32,42,0.08)',
          borderRadius: 20,
          padding: '1.4rem 1.4rem 1.2rem',
          boxShadow: '0 20px 40px rgba(31,41,55,0.08)',
          backdropFilter: 'blur(6px)',
        }}
      >
        <h1 style={{ margin: 0, fontSize: '2rem', letterSpacing: '-0.03em' }}>OnPoint Central Portal</h1>
        <p style={{ margin: '0.65rem 0 0', color: '#3f4a5b' }}>
          Unified entrypoint for training, productivity, finance, and AI tools.
        </p>
        <div style={{ marginTop: '0.65rem', color: '#3f4a5b', fontSize: '0.92rem' }}>
          Access mode:{' '}
          <strong>{authEnabled ? 'KEYCLOAK PROTECTED' : 'OPEN (DEV MODE)'}</strong>
          {session?.user?.name ? ` · Signed in as ${session.user.name}` : ''}
        </div>
        <div style={{ marginTop: '0.9rem', color: '#223045', fontSize: '0.95rem' }}>
          Aggregated health:{' '}
          <strong style={{ color: health?.status === 'ok' ? '#14663f' : '#8b2f12' }}>
            {health?.status?.toUpperCase() || 'UNKNOWN'}
          </strong>
        </div>
      </section>

      <section
        style={{
          maxWidth: 1100,
          margin: '1rem auto 0',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '0.8rem',
        }}
      >
        {portalLinks.map((item) => {
          const service = health?.services?.[item.key];
          const up = service?.status === 'up';
          const isInformational = item.key === 'frontend';
          return (
            <a
              key={item.key}
              href={item.url}
              target="_blank"
              rel="noreferrer"
              style={{
                display: 'block',
                textDecoration: 'none',
                color: '#182233',
                background: 'rgba(255,255,255,0.9)',
                borderRadius: 16,
                border: `1px solid ${isInformational ? 'rgba(56,93,132,0.28)' : up ? 'rgba(14,104,71,0.35)' : 'rgba(131,24,24,0.25)'}`,
                padding: '0.95rem 1rem',
                boxShadow: '0 10px 22px rgba(17,24,39,0.06)',
              }}
            >
              <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#607087' }}>{item.tag}</div>
              <div style={{ fontSize: '1rem', fontWeight: 700, marginTop: 2 }}>{item.title}</div>
              <div style={{ marginTop: 7, fontSize: '0.85rem', color: '#2d3a4c' }}>
                {isInformational
                  ? 'ENTRYPOINT · THIS PAGE'
                  : service
                  ? `${service.status.toUpperCase()}${service.status_code ? ` · HTTP ${service.status_code}` : ''}${typeof service.response_time_ms === 'number' ? ` · ${service.response_time_ms} ms` : ''}`
                  : 'Status unavailable'}
              </div>
            </a>
          );
        })}
      </section>
    </main>
  );
}
