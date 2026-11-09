# Komodo Env Setup

Use Docker Compose with a dedicated env file per environment.

## 1) Choose template

- Development: copy `.env.dev.example` to `.env`
- Production: copy `.env.prod.example` to `.env` and replace placeholders

## 2) Required secret rotation before prod

- `POSTGRES_PASSWORD`
- `KEYCLOAK_ADMIN_PASSWORD`
- `NEXTAUTH_SECRET`
- `KEYCLOAK_FRONTEND_CLIENT_SECRET`
- `N8N_ENCRYPTION_KEY`
- `VIKUNJA_SERVICE_SECRET`
- `OUTLINE_SECRET_KEY`
- `OUTLINE_UTILS_SECRET`
- `MEILI_MASTER_KEY`
- `APPSMITH_ENCRYPTION_PASSWORD`
- `GOTIFY_DEFAULTUSER_PASS`
- `NOCODB_AUTH_JWT_SECRET`

## 3) Startup

For a Git-based Komodo deployment, create a Stack from this repository and use
`docker-compose.yml` as the Compose file. For production, include
`docker-compose.prod.yml` as the second Compose file. Set the variables from
`.env.prod.example` in Komodo's environment/secret settings; do not commit a
populated `.env` file. The backend and frontend images build directly from the
tracked Dockerfiles in the repository, and the other services use their
upstream container images. Compose also builds a database bootstrap image from
`database-init/`; it creates the Outline and Vikunja databases idempotently,
including when the Postgres data volume already exists. No host-side init
script or manual image build is required.

The production override joins proxy-facing services to the external Docker
network `nginx_default`. Ensure the reverse-proxy stack creates that network on
the same Docker host before deploying this stack.

Run in the project root:

```bash
docker compose --env-file .env up -d
```

For production-hardening mode (recommended for Komodo):

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env up -d
```

This override:
- switches Keycloak out of dev startup mode
- removes host port exposure for internal services
- removes backend source bind mount and disables reload mode
- requires critical auth/search vars to be set
- attaches proxy-facing services to external Docker network `nginx_default`

If your reverse-proxy stack uses network `nginx_default`, ensure it exists before deploy:

```bash
docker network create nginx_default || true
```

## 4) Current optional component status

- MinIO was removed from the stack.
- NocoDB was added at `http://localhost:8088` for local development.

## 5) Global search bootstrap

After services are up and Keycloak is configured, call the backend indexing endpoint once to seed Meilisearch:

```bash
curl -X POST https://api.example.com/api/search/reindex \
	-H "Authorization: Bearer <portal_access_token>"
```

Query endpoint:

```bash
curl "https://api.example.com/api/search?q=docs&limit=20" \
	-H "Authorization: Bearer <portal_access_token>"
```

## 6) Pre-deploy smoke checks

Run the curl-based smoke suite before/after updates:

```bash
./scripts/smoke-check.sh
```

Optional authenticated checks (recommended in prod):

```bash
SMOKE_API_BASE_URL=https://api.example.com \
SMOKE_PORTAL_BASE_URL=https://portal.example.com \
SMOKE_OUTLINE_URL=https://docs.example.com \
SMOKE_BEARER_TOKEN=<portal_access_token> \
./scripts/smoke-check.sh
```

Behavior:
- exits non-zero on first hard failure (good for Komodo go/no-go gates)
- verifies auth is enforced on protected endpoints
- when token is provided, validates `/api/me`, search reindex, and search query
