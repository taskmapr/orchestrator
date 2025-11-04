"""Authentication utilities for Supabase JWT verification."""

from typing import Optional, Dict, Any
from types import SimpleNamespace
import jwt
from jwt import PyJWKClient
from fastapi import HTTPException

from app.config import (
    DISABLE_AUTH,
    SUPABASE_JWT_SECRET,
    SUPABASE_JWT_AUDIENCE,
    SUPABASE_JWT_ALGORITHMS,
    SUPABASE_URL,
    SUPABASE_API_KEY_FOR_JWKS,
)


# Initialize JWKS client for new signing keys system
jwks_client = None
if SUPABASE_URL:
    jwks_url = f"{SUPABASE_URL.rstrip('/')}/auth/v1/jwks"
    headers = None
    if SUPABASE_API_KEY_FOR_JWKS:
        auth_header = f"Bearer {SUPABASE_API_KEY_FOR_JWKS}"
        headers = {
            "apikey": SUPABASE_API_KEY_FOR_JWKS,
            "Authorization": auth_header,
        }
    jwks_client = PyJWKClient(jwks_url, cache_keys=True, headers=headers)


def _resolve_bearer_token(
    authorization_header: Optional[str],
    *,
    access_token: Optional[str] = None,
) -> str:
    """Extract bearer token from Authorization header or access_token parameter."""
    if authorization_header:
        scheme, _, value = authorization_header.partition(" ")
        if scheme.lower() != "bearer" or not value:
            raise HTTPException(401, "Authorization header must be a Bearer token")
        return value.strip()

    if access_token:
        token = access_token.strip()
        if token:
            return token

    raise HTTPException(401, "Missing Supabase access token")


def _decode_supabase_jwt(token: str) -> Dict[str, Any]:
    """Decode and verify Supabase JWT using JWKS (new system) or secret (legacy)."""
    decode_kwargs: Dict[str, Any] = {"algorithms": SUPABASE_JWT_ALGORITHMS}
    if SUPABASE_JWT_AUDIENCE:
        audience = [aud.strip() for aud in SUPABASE_JWT_AUDIENCE.split(",") if aud.strip()]
        if audience:
            decode_kwargs["audience"] = audience if len(audience) > 1 else audience[0]

    # Try new JWKS-based verification first (for asymmetric keys)
    if jwks_client:
        try:
            # Get the signing key from JWKS endpoint
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            return jwt.decode(
                token,
                signing_key.key,
                **decode_kwargs
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(401, "Supabase token expired")
        except jwt.InvalidAudienceError:
            raise HTTPException(401, "Supabase token has an invalid audience")
        except jwt.InvalidTokenError as e:
            # If JWKS verification fails and we have a secret, try legacy verification
            if not SUPABASE_JWT_SECRET:
                raise HTTPException(401, f"Supabase token is invalid: {str(e)}")
            # Fall through to legacy verification below
        except Exception as e:
            # JWKS fetch failed, try legacy if available
            if not SUPABASE_JWT_SECRET:
                raise HTTPException(500, f"JWT verification failed: {str(e)}")
            # Fall through to legacy verification below

    # Legacy verification with shared secret
    if SUPABASE_JWT_SECRET:
        try:
            return jwt.decode(token, SUPABASE_JWT_SECRET, **decode_kwargs)
        except jwt.ExpiredSignatureError:
            raise HTTPException(401, "Supabase token expired")
        except jwt.InvalidAudienceError:
            raise HTTPException(401, "Supabase token has an invalid audience")
        except jwt.InvalidTokenError as e:
            raise HTTPException(401, f"Supabase token is invalid: {str(e)}")
    
    raise HTTPException(500, "No JWT verification method configured (need SUPABASE_URL or SUPABASE_JWT_SECRET)")


def authenticate_supabase_user(
    authorization_header: Optional[str],
    *,
    access_token: Optional[str] = None,
) -> SimpleNamespace:
    """
    Authenticate and decode Supabase JWT token.
    
    If DISABLE_AUTH is set, bypasses authentication and returns a test user.
    
    Returns:
        SimpleNamespace with token, user_id, and claims
    """
    # Bypass authentication if DISABLE_AUTH is enabled
    if DISABLE_AUTH:
        return SimpleNamespace(
            token="test-token",
            user_id="test-user-dev",
            claims={"sub": "test-user-dev", "role": "authenticated"}
        )
    
    token = _resolve_bearer_token(authorization_header, access_token=access_token)
    payload = _decode_supabase_jwt(token)

    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise HTTPException(401, "Supabase token missing subject")

    return SimpleNamespace(token=token, user_id=str(user_id), claims=payload)
