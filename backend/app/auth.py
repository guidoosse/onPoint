from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.request import urlopen

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt


security = HTTPBearer(auto_error=False)


@dataclass
class AuthSettings:
    enabled: bool
    issuer: str
    audience: str
    jwks_url: str
    required_roles: list[str]


_JWKS_CACHE: dict[str, Any] = {"payload": None, "expires_at": 0.0}


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _auth_settings() -> AuthSettings:
    issuer = os.getenv("KEYCLOAK_ISSUER", "http://keycloak:8080/realms/onpoint")
    default_jwks = f"{issuer.rstrip('/')}/protocol/openid-connect/certs"
    required_roles = [
        role.strip()
        for role in os.getenv("KEYCLOAK_REQUIRED_ROLES", "").split(",")
        if role.strip()
    ]
    return AuthSettings(
        enabled=_as_bool(os.getenv("AUTH_ENABLED"), default=False),
        issuer=issuer,
        audience=os.getenv("KEYCLOAK_AUDIENCE", "onpoint-backend"),
        jwks_url=os.getenv("KEYCLOAK_JWKS_URL", default_jwks),
        required_roles=required_roles,
    )


def _fetch_jwks(jwks_url: str) -> dict[str, Any]:
    now = time.time()
    if _JWKS_CACHE["payload"] and _JWKS_CACHE["expires_at"] > now:
        return _JWKS_CACHE["payload"]

    with urlopen(jwks_url, timeout=3.0) as response:
        payload = json.loads(response.read().decode("utf-8"))

    _JWKS_CACHE["payload"] = payload
    _JWKS_CACHE["expires_at"] = now + 300
    return payload


def _has_required_roles(claims: dict[str, Any], required_roles: list[str]) -> bool:
    if not required_roles:
        return True

    realm_roles = claims.get("realm_access", {}).get("roles", [])
    resource_roles = []
    for _, client_data in claims.get("resource_access", {}).items():
        resource_roles.extend(client_data.get("roles", []))

    token_roles = set(realm_roles) | set(resource_roles)
    return all(role in token_roles for role in required_roles)


def verify_access_token(token: str) -> dict[str, Any]:
    settings = _auth_settings()

    if not settings.enabled:
        return {"sub": "dev-user", "preferred_username": "dev-user", "roles": ["developer"]}

    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token key id")

        jwks = _fetch_jwks(settings.jwks_url)
        key = next((item for item in jwks.get("keys", []) if item.get("kid") == kid), None)
        if not key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Signing key not found")

        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.audience,
            issuer=settings.issuer,
            options={"verify_at_hash": False},
        )
    except JWTError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid access token: {error}",
        ) from error

    if not _has_required_roles(claims, settings.required_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient role permissions",
        )

    return claims


def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any]:
    settings = _auth_settings()
    if not settings.enabled:
        return {"sub": "dev-user", "preferred_username": "dev-user", "roles": ["developer"]}

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    return verify_access_token(credentials.credentials)