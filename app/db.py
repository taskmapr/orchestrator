"""Database configuration and session management."""

import ssl
import os
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy import text

try:
    import certifi
except ImportError:
    certifi = None

from app.config import (
    SUPABASE_DB_URL,
    SUPABASE_DB_SSL_ROOT_CERT,
    SUPABASE_DB_SSL_ROOT_CERT_DATA,
    SUPABASE_DB_ALLOW_INVALID_SSL,
    SUPABASE_CA_BUNDLE,
    DB_TIMEOUT,
    SUPABASE_DB_DISABLED,
)

if not SUPABASE_DB_DISABLED and SUPABASE_DB_URL:
    from agents.extensions.memory.sqlalchemy_session import SQLAlchemySession
else:  # In disabled mode, avoid importing heavy dependencies
    SQLAlchemySession = None  # type: ignore[assignment]


# Configure asyncpg to use SSL if connecting to Supabase
connect_args: Dict[str, Any] = {}
if DB_TIMEOUT is not None:
    connect_args["timeout"] = DB_TIMEOUT

if SUPABASE_DB_DISABLED or not SUPABASE_DB_URL:
    engine: Optional[AsyncEngine] = None
else:
    if "supabase" in SUPABASE_DB_URL.lower():
        # Supabase requires TLS; asyncpg accepts a bool or SSLContext here.
        if SUPABASE_DB_ALLOW_INVALID_SSL:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        else:
            cafile = SUPABASE_DB_SSL_ROOT_CERT
            if cafile and not os.path.isfile(cafile):
                print(f"Warning: SUPABASE_DB_SSL_ROOT_CERT path not found: {cafile}")
                cafile = None
            if not cafile and certifi:
                cafile = certifi.where()
            ssl_context = ssl.create_default_context(cafile=cafile) if cafile else ssl.create_default_context()
            if SUPABASE_DB_SSL_ROOT_CERT_DATA:
                ssl_context.load_verify_locations(cadata=SUPABASE_DB_SSL_ROOT_CERT_DATA)
            if SUPABASE_CA_BUNDLE:
                ssl_context.load_verify_locations(cadata=SUPABASE_CA_BUNDLE)
        connect_args["ssl"] = ssl_context

    # Create database engine
    engine = create_async_engine(
        SUPABASE_DB_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        connect_args=connect_args,
    )


async def ensure_session_row(session_key: str, user_id: str):
    """
    Ensures a row exists in public.agent_sessions with (session_id, user_id).
    Matches the simple schema below; adapt if you've customised table names/columns.
    """
    if engine is None:
        return
    try:
        query = text("""
            insert into public.agent_sessions (session_id, user_id)
            values (:session_id, :user_id)
            on conflict (session_id) do nothing
        """)
        async with engine.begin() as conn:
            await conn.execute(query, {"session_id": session_key, "user_id": user_id})
    except Exception as e:
        # Log but don't fail - allow testing without database
        print(f"Warning: Could not ensure session row: {e}")


def make_sqlalchemy_session(session_key: str) -> Optional["SQLAlchemySession"]:
    """
    Agents SDK memory backend that writes/reads items from Supabase Postgres via SQLAlchemy.
    Set create_tables=True in dev to auto-create; prefer migrations in prod.
    """
    if engine is None or SQLAlchemySession is None:
        return None
    try:
        return SQLAlchemySession(
            session_id=session_key,
            engine=engine,
            create_tables=True,   # Let SDK create tables with correct schema
        )
    except Exception as e:
        # Log but don't fail - allow testing without database
        print(f"Warning: Could not create SQLAlchemySession: {e}")
        return None
