from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from time import perf_counter
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import Depends, FastAPI, HTTPException, Query, status

from app.auth import require_auth

app = FastAPI(
    title="OnPoint Portal",
    version="0.1.0",
    description="Unified tracking portal for health, training, consultancy, accounting and relationship management.",
)

MEILI_HOST = os.getenv("MEILI_HOST", "http://meilisearch:7700")
MEILI_MASTER_KEY = os.getenv("MEILI_MASTER_KEY", "")
MEILI_INDEX = os.getenv("MEILI_INDEX", "portal_services")


SERVICE_ENDPOINTS: dict[str, str] = {
    "backend": "http://backend:8000/health",
    "outline": "http://outline:3000/",
    "vikunja": "http://vikunja:3456/api/v1/info",
    "n8n": "http://n8n:5678/healthz",
    "keycloak": "http://keycloak:8080/",
    "open_webui": "http://open-webui:8080/",
    "meilisearch": "http://meilisearch:7700/health",
    "appsmith": "http://appsmith:80/",
    "gotify": "http://gotify:80/",
    "stirling_pdf": "http://stirling-pdf:8080/",
    "nocodb": "http://nocodb:8080/",
}

SERVICE_CATALOG: list[dict[str, str]] = [
    {
        "key": "outline",
        "title": "Outline",
        "url": "http://localhost:3000",
        "tag": "knowledge",
        "description": "Team knowledge base and wiki",
    },
    {
        "key": "backend",
        "title": "FastAPI",
        "url": "http://localhost:8000/docs",
        "tag": "api",
        "description": "Core API for OnPoint modules",
    },
    {
        "key": "keycloak",
        "title": "Keycloak",
        "url": "http://localhost:8080",
        "tag": "auth",
        "description": "Identity and access management",
    },
    {
        "key": "vikunja",
        "title": "Vikunja",
        "url": "http://localhost:3456",
        "tag": "tasks",
        "description": "Task and project management",
    },
    {
        "key": "n8n",
        "title": "n8n",
        "url": "http://localhost:5678",
        "tag": "automation",
        "description": "Workflow automation and integrations",
    },
    {
        "key": "open_webui",
        "title": "Open WebUI",
        "url": "http://localhost:3002",
        "tag": "ai",
        "description": "LLM chat and AI workspace",
    },
    {
        "key": "meilisearch",
        "title": "Meilisearch",
        "url": "http://localhost:7700",
        "tag": "search",
        "description": "Global search index and retrieval",
    },
    {
        "key": "appsmith",
        "title": "Appsmith",
        "url": "http://localhost:8085",
        "tag": "apps",
        "description": "Low-code internal app builder",
    },
    {
        "key": "gotify",
        "title": "Gotify",
        "url": "http://localhost:8086",
        "tag": "notify",
        "description": "Push notifications and alerting",
    },
    {
        "key": "stirling_pdf",
        "title": "Stirling PDF",
        "url": "http://localhost:8087",
        "tag": "documents",
        "description": "PDF conversion and document operations",
    },
    {
        "key": "nocodb",
        "title": "NocoDB",
        "url": "http://localhost:8088",
        "tag": "data",
        "description": "No-code data apps over SQL tables",
    },
]


def _probe_http(url: str, timeout_seconds: float = 1.5) -> dict[str, Any]:
    started = perf_counter()
    request = Request(url, method="GET")
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            status_code = response.getcode() or 0
            duration_ms = round((perf_counter() - started) * 1000, 1)
            return {
                "status": "up" if status_code < 500 else "down",
                "status_code": status_code,
                "response_time_ms": duration_ms,
            }
    except HTTPError as error:
        duration_ms = round((perf_counter() - started) * 1000, 1)
        return {
            "status": "up" if error.code < 500 else "down",
            "status_code": error.code,
            "response_time_ms": duration_ms,
            "error": str(error),
        }
    except (TimeoutError, URLError, OSError) as error:
        duration_ms = round((perf_counter() - started) * 1000, 1)
        return {
            "status": "down",
            "status_code": None,
            "response_time_ms": duration_ms,
            "error": str(error),
        }


def _meili_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if MEILI_MASTER_KEY:
        headers["Authorization"] = f"Bearer {MEILI_MASTER_KEY}"
    return headers


def _meili_request(path: str, method: str = "GET", payload: Any | None = None) -> Any:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(f"{MEILI_HOST.rstrip('/')}{path}", data=body, method=method)
    for key, value in _meili_headers().items():
        request.add_header(key, value)

    try:
        with urlopen(request, timeout=4.0) as response:
            content = response.read().decode("utf-8")
            return json.loads(content) if content else {}
    except HTTPError as error:
        detail = error.reason
        try:
            content = error.read().decode("utf-8")
            parsed = json.loads(content)
            detail = parsed.get("message", detail)
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Meilisearch request failed: {detail}",
        ) from error
    except (URLError, TimeoutError, OSError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Cannot reach Meilisearch: {error}",
        ) from error


def _ensure_meili_index() -> None:
    indexes = _meili_request("/indexes?limit=1000", method="GET")
    existing = {item.get("uid") for item in indexes.get("results", []) if isinstance(item, dict)}
    if MEILI_INDEX not in existing:
        _meili_request(
            "/indexes",
            method="POST",
            payload={"uid": MEILI_INDEX, "primaryKey": "id"},
        )


def _wait_meili_task(task_uid: int, timeout_seconds: float = 20.0) -> dict[str, Any]:
    started = perf_counter()
    last_result: dict[str, Any] = {}
    while (perf_counter() - started) < timeout_seconds:
        last_result = _meili_request(f"/tasks/{task_uid}", method="GET")
        task_status = last_result.get("status")
        if task_status == "succeeded":
            return last_result
        if task_status in {"failed", "canceled"}:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Meilisearch task {task_uid} {task_status}: {last_result}",
            )

    raise HTTPException(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        detail=f"Meilisearch task {task_uid} did not complete within timeout",
    )


def _build_search_documents() -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    for service in SERVICE_CATALOG:
        key = service["key"]
        health_source = SERVICE_ENDPOINTS.get(key)
        health_data = _probe_http(health_source) if health_source else {
            "status": "unknown",
            "status_code": None,
            "response_time_ms": None,
        }
        documents.append(
            {
                "id": key,
                "key": key,
                "title": service["title"],
                "url": service["url"],
                "tag": service["tag"],
                "description": service["description"],
                "health_status": health_data.get("status"),
                "health_status_code": health_data.get("status_code"),
                "health_response_time_ms": health_data.get("response_time_ms"),
                "search_blob": " ".join(
                    [
                        service["title"],
                        service["tag"],
                        service["description"],
                        key,
                    ]
                ),
            }
        )
    return documents


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/modules")
def list_modules(_: dict[str, Any] = Depends(require_auth)) -> dict[str, list[str]]:
    return {
        "modules": [
            "dog_training",
            "running",
            "karate",
            "consultancy",
            "accounting",
            "personal_relations",
            "ai_planning",
        ]
    }


@app.get("/api/services/health")
def service_health() -> dict[str, Any]:
    checks: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=len(SERVICE_ENDPOINTS)) as executor:
        futures = {
            executor.submit(_probe_http, url): (name, url)
            for name, url in SERVICE_ENDPOINTS.items()
        }
        for future in as_completed(futures):
            name, url = futures[future]
            result = future.result()
            checks[name] = {
                "url": url,
                **result,
            }

    down_services = [name for name, result in checks.items() if result["status"] != "up"]
    return {
        "status": "degraded" if down_services else "ok",
        "down_services": down_services,
        "services": checks,
    }


@app.post("/api/search/reindex")
def reindex_services_for_search(_: dict[str, Any] = Depends(require_auth)) -> dict[str, Any]:
    documents = _build_search_documents()
    _ensure_meili_index()
    index_task = _meili_request(
        f"/indexes/{MEILI_INDEX}/documents?primaryKey=id",
        method="POST",
        payload=documents,
    )
    settings_task = _meili_request(
        f"/indexes/{MEILI_INDEX}/settings/searchable-attributes",
        method="PUT",
        payload=["title", "tag", "description", "search_blob", "key"],
    )
    index_task_uid = int(index_task.get("taskUid", 0))
    settings_task_uid = int(settings_task.get("taskUid", 0))
    if index_task_uid:
        _wait_meili_task(index_task_uid)
    if settings_task_uid:
        _wait_meili_task(settings_task_uid)

    return {
        "status": "ok",
        "index": MEILI_INDEX,
        "indexed_documents": len(documents),
    }


@app.get("/api/search")
def search_services(
    q: str = Query(default="", min_length=0),
    limit: int = Query(default=20, ge=1, le=100),
    _: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    results = _meili_request(
        f"/indexes/{MEILI_INDEX}/search",
        method="POST",
        payload={"q": q, "limit": limit},
    )
    return {
        "index": MEILI_INDEX,
        "query": q,
        "results": results,
    }


@app.get("/api/me")
def who_am_i(user: dict[str, Any] = Depends(require_auth)) -> dict[str, Any]:
    return {
        "sub": user.get("sub"),
        "preferred_username": user.get("preferred_username"),
        "email": user.get("email"),
        "realm_roles": user.get("realm_access", {}).get("roles", []),
    }


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Welcome to the OnPoint portal"}
