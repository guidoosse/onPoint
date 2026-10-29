# Keycloak Production Checklist

This project is now prepared for Keycloak-backed API protection. Use this checklist when deploying to cloud.

## 1) Network and ingress model

- Expose services behind one HTTPS domain (example: portal.example.com).
- Keep internal service ports private (Docker/Kubernetes network only).
- Route with paths or subdomains, for example:
  - portal.example.com -> frontend
  - api.portal.example.com -> backend
  - id.portal.example.com -> keycloak
  - outline.portal.example.com -> outline
  - tasks.portal.example.com -> vikunja

## 2) Keycloak realm setup

- Create realm: onpoint
- Create realm roles:
  - portal_user
  - portal_admin
  - automation_user (optional)
- Create groups and map default roles:
  - users -> portal_user
  - admins -> portal_admin

## 3) Keycloak clients

Create one client per relying service.

- Backend API client (confidential):
  - Client ID: onpoint-backend
  - Access type: confidential
  - Service accounts: optional
  - Audience used by backend: onpoint-backend

- Frontend client (public or confidential with BFF):
  - Client ID: onpoint-frontend
  - Standard flow enabled
  - Valid redirect URIs: https://portal.example.com/*
  - Valid post logout redirect URIs: https://portal.example.com/*
  - Web origins: https://portal.example.com

- Optional service clients:
  - outline
  - vikunja
  - n8n
  - open-webui

## 4) Backend environment values

Set these in production (examples):

- AUTH_ENABLED=true
- KEYCLOAK_AUDIENCE=onpoint-backend
- KEYCLOAK_ISSUER=https://id.portal.example.com/realms/onpoint
- KEYCLOAK_JWKS_URL=https://id.portal.example.com/realms/onpoint/protocol/openid-connect/certs
- KEYCLOAK_REQUIRED_ROLES=portal_user

## 4b) Frontend environment values

Set these in production for the Next.js portal:

- FRONTEND_AUTH_ENABLED=true
- NEXTAUTH_URL=https://portal.example.com
- NEXTAUTH_SECRET=<long-random-secret>
- KEYCLOAK_FRONTEND_CLIENT_ID=onpoint-frontend
- KEYCLOAK_FRONTEND_CLIENT_SECRET=<frontend-client-secret>
- KEYCLOAK_FRONTEND_ISSUER=https://id.portal.example.com/realms/onpoint

Result:
- The portal homepage is protected by Keycloak session auth.
- Unauthenticated users are redirected to Keycloak sign-in.

Notes:
- AUTH_ENABLED=false keeps dev mode (no JWT required).
- KEYCLOAK_REQUIRED_ROLES can contain multiple comma-separated roles.

## 5) Validate backend auth in prod

Use an access token minted by Keycloak for onpoint-backend audience.

- /api/me should return user identity claims.
- /api/modules should require bearer token.
- /health and /api/services/health can remain public for monitoring, or be protected at ingress.

## 6) Service-by-service access control

Do not rely only on hidden links in frontend. Enforce auth per service.

- Outline:
  - Configure OIDC/Keycloak integration in Outline settings.
  - Restrict signups/invites according to your org policy.

- Vikunja:
  - Configure OIDC provider and disable open registration if desired.

- n8n:
  - Enable auth mode (OIDC or secure basic auth) before exposing publicly.

- Open WebUI:
  - Enable built-in auth and/or OIDC if supported by your selected version.

- Keycloak admin:
  - Never expose admin endpoints without IP/VPN restrictions and strong admin policy.

## 7) Ingress hardening

- Enforce TLS and HSTS.
- Add IP allow-list or VPN for admin surfaces.
- Add rate limiting and WAF controls.
- Set strict CORS per domain.
- Keep cookies secure/HttpOnly/SameSite where applicable.

## 8) Rollout strategy

1. Deploy with AUTH_ENABLED=false and verify app health.
2. Configure Keycloak realm, roles, and clients.
3. Issue test user and token.
4. Enable AUTH_ENABLED=true in backend.
5. Verify /api/me and protected API paths.
6. Lock down each service UI with OIDC before public exposure.
7. Remove direct public port exposure for internal services.

## 9) Emergency fallback

- Keep a break-glass admin path documented (private network only).
- Preserve ability to rotate client secrets quickly.
- Keep auth flags and secrets in a secure secret manager (not in git).
