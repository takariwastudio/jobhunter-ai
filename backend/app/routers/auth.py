import uuid
import hashlib
import secrets
import base64
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])
settings = get_settings()

SUPABASE_AUTH = f"{settings.SUPABASE_URL}/auth/v1"
_AUTH_HEADERS = {
    "apikey": settings.SUPABASE_ANON_KEY,
    "Content-Type": "application/json",
}

SUPPORTED_PROVIDERS = {"google", "github", "azure", "facebook", "twitter"}

# ---------------------------------------------------------------------------
# JWT verification — supports ES256 (current Supabase default) and HS256 (legacy)
# JWKS are cached in-process; refresh on key-not-found to handle key rotation.
# ---------------------------------------------------------------------------

_jwks_cache: list[dict] | None = None

_ERR_INVALID_TOKEN = "Token inválido o expirado"


async def _get_jwks() -> list[dict]:
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{SUPABASE_AUTH}/.well-known/jwks.json", timeout=5)
            res.raise_for_status()
            _jwks_cache = res.json().get("keys", [])
    return _jwks_cache


async def _verify_jwt(token: str) -> dict:
    """Verify a Supabase JWT — ES256 (JWKS) or HS256 (legacy secret).

    Reading the unverified header first is the standard JWKS key-selection
    pattern: we use it only to pick the correct public key, then the
    signature is fully verified by jwt.decode() below.
    """
    try:
        header = jwt.get_unverified_header(token)  # NOSONAR — header read only for key selection
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token malformado")

    alg = header.get("alg", "ES256")

    if alg == "HS256":
        if not settings.SUPABASE_JWT_SECRET:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Legacy JWT secret no configurado")
        try:
            return jwt.decode(token, settings.SUPABASE_JWT_SECRET, algorithms=["HS256"],
                              options={"verify_aud": False})
        except JWTError:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, _ERR_INVALID_TOKEN)

    # ES256 — verify against JWKS public keys
    kid = header.get("kid")
    keys = await _get_jwks()
    key = next((k for k in keys if k.get("kid") == kid), None)

    if key is None:
        # Key not in cache — may have rotated; refresh once
        global _jwks_cache
        _jwks_cache = None
        keys = await _get_jwks()
        key = next((k for k in keys if k.get("kid") == kid), None)

    if key is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Clave JWT no encontrada")

    try:
        return jwt.decode(token, key, algorithms=["ES256"], options={"verify_aud": False})
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, _ERR_INVALID_TOKEN)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class EmailPasswordBody(BaseModel):
    email: EmailStr
    password: str


class RegisterBody(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class UserResponse(BaseModel):
    id: str
    email: str | None
    phone: str | None
    display_name: str | None
    avatar_url: str | None
    provider: str

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cookie_opts(max_age: int) -> dict:
    return {
        "httponly": True,
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE,
        "max_age": max_age,
        "path": "/",
    }


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str, expires_in: int = 3600) -> None:
    response.set_cookie("access_token", access_token, **_cookie_opts(expires_in))
    response.set_cookie("refresh_token", refresh_token, **_cookie_opts(60 * 60 * 24 * 60))  # 60 days


def _clear_auth_cookies(response: Response) -> None:
    for name in ("access_token", "refresh_token", "oauth_pkce"):
        response.delete_cookie(name, path="/")


def _verify_jwt(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido o expirado")


def _generate_pkce() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return verifier, challenge


async def _sync_user(db: AsyncSession, supabase_user: dict) -> User:
    """Upsert Supabase user into local users table."""
    user_id = uuid.UUID(supabase_user["id"])
    metadata = supabase_user.get("user_metadata") or {}
    app_meta = supabase_user.get("app_metadata") or {}

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            id=user_id,
            email=supabase_user.get("email"),
            phone=supabase_user.get("phone"),
            display_name=metadata.get("full_name") or metadata.get("name"),
            avatar_url=metadata.get("avatar_url") or metadata.get("picture"),
            provider=app_meta.get("provider", "email"),
        )
        db.add(user)
    else:
        user.email = supabase_user.get("email") or user.email
        user.phone = supabase_user.get("phone") or user.phone
        user.display_name = (
            metadata.get("full_name") or metadata.get("name") or user.display_name
        )
        user.avatar_url = (
            metadata.get("avatar_url") or metadata.get("picture") or user.avatar_url
        )

    await db.commit()
    await db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Dependency — used by all protected routes
# ---------------------------------------------------------------------------

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No autenticado")

    payload = await _verify_jwt(token)
    user_id = uuid.UUID(payload["sub"])

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario no encontrado")

    return user


# ---------------------------------------------------------------------------
# Email / Password
# ---------------------------------------------------------------------------

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterBody, response: Response, db: AsyncSession = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{SUPABASE_AUTH}/signup",
            json={
                "email": body.email,
                "password": body.password,
                "data": {"full_name": body.full_name},
            },
            headers=_AUTH_HEADERS,
        )
    if res.status_code >= 400:
        detail = res.json().get("msg") or res.json().get("message") or "Error al registrarse"
        raise HTTPException(res.status_code, detail)

    data = res.json()
    session = data.get("session")

    if session:
        _set_auth_cookies(response, session["access_token"], session["refresh_token"], session.get("expires_in", 3600))
        user = await _sync_user(db, data["user"])
    else:
        # Email confirmation required — no session yet
        user_data = data.get("user") or {}
        user_id = uuid.UUID(user_data["id"]) if user_data.get("id") else uuid.uuid4()
        result = await db.execute(select(User).where(User.id == user_id))
        existing = result.scalar_one_or_none()
        if not existing:
            user = User(id=user_id, email=body.email, display_name=body.full_name)
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            user = existing

    return user


@router.post("/login", response_model=UserResponse)
async def login(body: EmailPasswordBody, response: Response, db: AsyncSession = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{SUPABASE_AUTH}/token",
            params={"grant_type": "password"},
            json={"email": body.email, "password": body.password},
            headers=_AUTH_HEADERS,
        )
    if res.status_code >= 400:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales incorrectas")

    data = res.json()
    _set_auth_cookies(response, data["access_token"], data["refresh_token"], data.get("expires_in", 3600))
    user = await _sync_user(db, data["user"])
    return user


# ---------------------------------------------------------------------------
# OAuth (PKCE flow — fully server-side, no tokens ever reach the browser)
# ---------------------------------------------------------------------------

@router.get("/oauth/{provider}")
async def oauth_redirect(provider: str, response: Response):
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Proveedor no soportado: {provider}")

    verifier, challenge = _generate_pkce()
    callback_url = f"{settings.BACKEND_URL}/api/v1/auth/callback"

    oauth_url = (
        f"{SUPABASE_AUTH}/authorize?"
        + urlencode({
            "provider": provider,
            "redirect_to": callback_url,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        })
    )

    redirect = RedirectResponse(oauth_url, status_code=302)
    redirect.set_cookie(
        "oauth_pkce", verifier,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=600,  # 10 min to complete OAuth
        path="/",
    )
    return redirect


@router.get("/callback")
async def oauth_callback(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    code = request.query_params.get("code")
    error = request.query_params.get("error")

    if error or not code:
        desc = request.query_params.get("error_description", "OAuth cancelado")
        return RedirectResponse(f"{settings.FRONTEND_URL}/login?error={desc}", status_code=302)

    verifier = request.cookies.get("oauth_pkce")
    if not verifier:
        return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=session_expired", status_code=302)

    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{SUPABASE_AUTH}/token",
            params={"grant_type": "pkce"},
            json={"auth_code": code, "code_verifier": verifier},
            headers=_AUTH_HEADERS,
        )

    if res.status_code >= 400:
        return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=auth_failed", status_code=302)

    data = res.json()
    user = await _sync_user(db, data["user"])

    redirect = RedirectResponse(f"{settings.FRONTEND_URL}/dashboard", status_code=302)
    _set_auth_cookies(redirect, data["access_token"], data["refresh_token"], data.get("expires_in", 3600))
    redirect.delete_cookie("oauth_pkce", path="/")
    return redirect


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user


@router.post("/refresh", response_model=UserResponse)
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sin refresh token")

    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{SUPABASE_AUTH}/token",
            params={"grant_type": "refresh_token"},
            json={"refresh_token": token},
            headers=_AUTH_HEADERS,
        )
    if res.status_code >= 400:
        _clear_auth_cookies(response)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sesión expirada")

    data = res.json()
    _set_auth_cookies(response, data["access_token"], data["refresh_token"], data.get("expires_in", 3600))
    user = await _sync_user(db, data["user"])
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response):
    token = request.cookies.get("access_token")
    if token:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{SUPABASE_AUTH}/logout",
                headers={**_AUTH_HEADERS, "Authorization": f"Bearer {token}"},
            )
    _clear_auth_cookies(response)
