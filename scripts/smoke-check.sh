#!/usr/bin/env sh
set -eu

# Curl-based smoke checks for Komodo pre/post deploy validation.
# Exit code is non-zero on the first hard failure (go/no-go gate).

fail() {
  echo "[FAIL] $1" >&2
  exit 1
}

pass() {
  echo "[PASS] $1"
}

warn() {
  echo "[WARN] $1"
}

check_http_ok() {
  name="$1"
  url="$2"

  code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time "${SMOKE_TIMEOUT:-20}" "$url" || true)"
  case "$code" in
    200|204|301|302|307|308)
      pass "$name ($url) -> HTTP $code"
      ;;
    *)
      fail "$name ($url) -> HTTP $code"
      ;;
  esac
}

check_http_auth_expected() {
  name="$1"
  url="$2"

  code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time "${SMOKE_TIMEOUT:-20}" "$url" || true)"
  case "$code" in
    401|403)
      pass "$name enforces auth ($url) -> HTTP $code"
      ;;
    *)
      fail "$name should enforce auth ($url) -> got HTTP $code"
      ;;
  esac
}

check_json_contains() {
  name="$1"
  url="$2"
  needle="$3"

  body="$(curl -sS --max-time "${SMOKE_TIMEOUT:-20}" "$url" || true)"
  echo "$body" | grep -q "$needle" || fail "$name missing expected marker '$needle'"
  pass "$name contains '$needle'"
}

api_base="${SMOKE_API_BASE_URL:-http://localhost:8000}"
portal_base="${SMOKE_PORTAL_BASE_URL:-http://localhost:3005}"
outline_url="${SMOKE_OUTLINE_URL:-http://localhost:3000}"
vikunja_url="${SMOKE_VIKUNJA_URL:-http://localhost:3456/api/v1/info}"
n8n_url="${SMOKE_N8N_URL:-http://localhost:5678/healthz}"
meili_url="${SMOKE_MEILI_URL:-http://localhost:7700/health}"
appsmith_url="${SMOKE_APPSMITH_URL:-http://localhost:8085}"
gotify_url="${SMOKE_GOTIFY_URL:-http://localhost:8086/health}"
stirling_url="${SMOKE_STIRLING_URL:-http://localhost:8087}"
nocodb_url="${SMOKE_NOCODB_URL:-http://localhost:8088}"

# Core availability checks.
check_http_ok "Portal" "$portal_base"
check_http_ok "Backend health" "$api_base/health"
check_http_ok "Outline" "$outline_url"
check_http_ok "Vikunja" "$vikunja_url"
check_http_ok "n8n" "$n8n_url"
check_http_ok "Meilisearch" "$meili_url"
check_http_ok "Appsmith" "$appsmith_url"
check_http_ok "Gotify" "$gotify_url"
check_http_ok "Stirling PDF" "$stirling_url"
check_http_ok "NocoDB" "$nocodb_url"

# Security posture checks.
check_http_auth_expected "Backend protected modules API" "$api_base/api/modules"

# Aggregated health should at least return JSON with a status key.
check_json_contains "Aggregated health" "$api_base/api/services/health" '"status"'

# Optional authenticated checks when token is supplied.
if [ "${SMOKE_BEARER_TOKEN:-}" != "" ]; then
  auth_header="Authorization: Bearer ${SMOKE_BEARER_TOKEN}"

  code_me="$(curl -sS -o /dev/null -w '%{http_code}' --max-time "${SMOKE_TIMEOUT:-20}" -H "$auth_header" "$api_base/api/me" || true)"
  [ "$code_me" = "200" ] || fail "Authenticated /api/me failed with HTTP $code_me"
  pass "Authenticated /api/me"

  code_reindex="$(curl -sS -o /dev/null -w '%{http_code}' --max-time "${SMOKE_TIMEOUT:-20}" -X POST -H "$auth_header" "$api_base/api/search/reindex" || true)"
  case "$code_reindex" in
    200|201|202)
      pass "Authenticated search reindex"
      ;;
    *)
      fail "Authenticated search reindex failed with HTTP $code_reindex"
      ;;
  esac

  code_search="$(curl -sS -o /dev/null -w '%{http_code}' --max-time "${SMOKE_TIMEOUT:-20}" -H "$auth_header" "$api_base/api/search?q=pdf&limit=5" || true)"
  [ "$code_search" = "200" ] || fail "Authenticated search query failed with HTTP $code_search"
  pass "Authenticated search query"
else
  warn "SMOKE_BEARER_TOKEN not set; skipped authenticated checks (/api/me, reindex, /api/search)."
fi

echo "[PASS] Smoke suite completed successfully."
