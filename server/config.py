"""Centralized server configuration and clients.

This module loads environment variables, exposes a configured Supabase
client, and provides helpers to verify Supabase JWTs and extract the
authenticated user id. Keeping this logic in one place lets FastAPI
dependencies import it without creating circular imports.
"""

from __future__ import annotations

import os
import logging
from typing import Optional, Tuple

from dotenv import load_dotenv

# Third‑party clients
from supabase import create_client, Client as SupabaseClient
import jwt
from jwt import InvalidTokenError

load_dotenv()  # load from .env when running locally

logger = logging.getLogger("config")


# ----- Environment -----
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
# If you enabled "JWT Secret" in API settings, set it here; otherwise the anon key
# can verify signatures for anon role only. Prefer the service_role key for backend
# database operations (never expose to frontend!).
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")

if not SUPABASE_URL or not SUPABASE_KEY:
	logger.warning("Supabase URL/KEY not set. Database features will be disabled until configured.")


def get_supabase_client() -> Optional[SupabaseClient]:
	"""Create a singleton Supabase client.

	Returns None if required envs are missing so that the app can still start
	in a limited demo mode.
	"""
	try:
		if not SUPABASE_URL or not SUPABASE_KEY:
			return None
		return create_client(SUPABASE_URL, SUPABASE_KEY)
	except Exception as e:
		logger.error(f"Failed to create Supabase client: {e}")
		return None


# Lazily initialized client; modules can import `supabase` from here
supabase: Optional[SupabaseClient] = get_supabase_client()


def verify_supabase_jwt(token: str) -> Tuple[bool, Optional[str], Optional[str]]:
	"""Verify a Supabase JWT and return (ok, user_id, error).

	This uses PyJWT locally with the configured SUPABASE_JWT_SECRET. If that
	secret isn't available (e.g., only anon key is provided), we attempt a
	lightweight validation by decoding without verify to extract the subject
	for downstream use. In production you should set SUPABASE_JWT_SECRET to
	the value shown in your Supabase project's API settings.
	"""
	if not token:
		return False, None, "Missing token"

	# Strip optional "Bearer " prefix if present
	if token.lower().startswith("bearer "):
		token = token.split(" ", 1)[1]

	try:
		if SUPABASE_JWT_SECRET:
			# Decode with verification, but don't verify audience (aud claim)
			# because frontend tokens have different audience than service_role
			payload = jwt.decode(
				token, 
				SUPABASE_JWT_SECRET, 
				algorithms=["HS256"],
				options={"verify_aud": False}  # Skip audience verification
			)
			user_id = payload.get("sub") or payload.get("user_id") or payload.get("uid")
			if not user_id:
				return False, None, "Token missing subject"
			return True, user_id, None
		else:
			# Fallback: decode without verifying signature (not recommended for prod)
			payload = jwt.decode(token, options={"verify_signature": False})
			user_id = payload.get("sub") or payload.get("user_id") or payload.get("uid")
			if user_id:
				logger.warning("JWT verified without signature check because SUPABASE_JWT_SECRET is not set.")
				return True, user_id, None
			return False, None, "Could not extract user id from token"
	except InvalidTokenError as e:
		return False, None, f"Invalid token: {e}"
	except Exception as e:
		logger.exception("JWT verification failed")
		return False, None, str(e)


__all__ = [
	"supabase",
	"get_supabase_client",
	"verify_supabase_jwt",
	"SUPABASE_URL",
	"SUPABASE_KEY",
	"SUPABASE_JWT_SECRET",
]