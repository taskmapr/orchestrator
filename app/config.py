"""Configuration and environment management."""

import os
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from dotenv import load_dotenv


# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


# Disable tracing to avoid span_data.result null errors
os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"


# Database Configuration
SUPABASE_DB_URL = os.environ["SUPABASE_DB_URL"]
SUPABASE_DB_SSL_ROOT_CERT = os.environ.get("SUPABASE_DB_SSL_ROOT_CERT")
SUPABASE_DB_SSL_ROOT_CERT_DATA = os.environ.get("SUPABASE_DB_SSL_ROOT_CERT_DATA")
SUPABASE_DB_ALLOW_INVALID_SSL = (
    os.environ.get("SUPABASE_DB_ALLOW_INVALID_SSL", "").strip().lower() in {"1", "true", "yes"}
)


# Supabase CA bundle
SUPABASE_CA_BUNDLE = """
"""


# Convert to asyncpg driver if needed
if "postgresql://" in SUPABASE_DB_URL and "postgresql+asyncpg://" not in SUPABASE_DB_URL:
    SUPABASE_DB_URL = SUPABASE_DB_URL.replace("postgresql://", "postgresql+asyncpg://")
    SUPABASE_DB_URL = SUPABASE_DB_URL.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
    SUPABASE_DB_URL = SUPABASE_DB_URL.replace("postgresql+psycopg://", "postgresql+asyncpg://")


# Parse and clean database URL
parts = urlsplit(SUPABASE_DB_URL)
timeout_value: float | None = None
if parts.query:
    query_params: list[tuple[str, str]] = []
    for k, v in parse_qsl(parts.query, keep_blank_values=True):
        lower = k.lower()
        if lower == "sslmode":
            continue
        if lower == "connect_timeout":
            try:
                timeout_value = float(v)
            except (TypeError, ValueError):
                pass
            continue
        query_params.append((k, v))
    new_query = urlencode(query_params, doseq=True)
    SUPABASE_DB_URL = urlunsplit(parts._replace(query=new_query))


# OpenAI Configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


# Supabase Auth Configuration
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET")
SUPABASE_JWT_AUDIENCE = os.environ.get("SUPABASE_JWT_AUDIENCE")
SUPABASE_JWT_ALGORITHMS = [
    algo.strip() 
    for algo in os.environ.get("SUPABASE_JWT_ALGORITHMS", "HS256,RS256").split(",") 
    if algo.strip()
]
if not SUPABASE_JWT_ALGORITHMS:
    SUPABASE_JWT_ALGORITHMS = ["HS256", "RS256"]

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_API_KEY_FOR_JWKS = (
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    or os.environ.get("SUPABASE_KEY")
    or os.environ.get("SUPABASE_ANON_KEY")
)


# MCP Configuration
MCP_BASE_URL = os.environ.get("MCP_BASE_URL", "http://127.0.0.1:8000")
MCP_SERVER_URL = f"{MCP_BASE_URL}/mcp/sse"


# Server Configuration
DB_TIMEOUT = timeout_value
