"""
Supabase client initialization and secure connection utilities for PocketTrack.
Supports Streamlit Secrets and environment variables.
"""
import os
from typing import Optional, Tuple
from supabase import create_client, Client


def _load_env_file(filepath: str = ".env") -> None:
    """Read a local .env file into os.environ if present, without overwriting."""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v
        except Exception:
            pass


def get_supabase_credentials() -> Tuple[Optional[str], Optional[str]]:
    """
    Retrieve Supabase project URL and anon/publishable key securely.
    Checks Streamlit Secrets first, then environment variables (including .env).

    Returns:
        (supabase_url, supabase_key)
    """
    url: Optional[str] = None
    key: Optional[str] = None

    # 1. Attempt reading from Streamlit Secrets
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            if "SUPABASE_URL" in st.secrets:
                url = st.secrets["SUPABASE_URL"]
            elif "supabase" in st.secrets and "url" in st.secrets["supabase"]:
                url = st.secrets["supabase"]["url"]

            if "SUPABASE_KEY" in st.secrets:
                key = st.secrets["SUPABASE_KEY"]
            elif "SUPABASE_ANON_KEY" in st.secrets:
                key = st.secrets["SUPABASE_ANON_KEY"]
            elif "supabase" in st.secrets and "key" in st.secrets["supabase"]:
                key = st.secrets["supabase"]["key"]
    except Exception:
        pass

    # 2. Fall back to environment variables (load .env if needed)
    if not url or not key:
        _load_env_file()
        if not url:
            url = os.getenv("SUPABASE_URL")
        if not key:
            key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")

    return url, key


def get_supabase_client() -> Client:
    """
    Initialize and return the Supabase client using configured credentials.

    Raises:
        ValueError: If SUPABASE_URL or SUPABASE_KEY is not configured.
    """
    url, key = get_supabase_credentials()

    if not url or not key:
        raise ValueError(
            "Supabase credentials are not configured. Please provide SUPABASE_URL "
            "and SUPABASE_KEY (anon/publishable key) via Streamlit secrets (.streamlit/secrets.toml) "
            "or environment variables (.env)."
        )

    return create_client(url, key)


def verify_connection() -> Tuple[bool, str]:
    """
    Verify connectivity to the Supabase project.

    Checks:
    1. Credentials presence.
    2. Network connectivity and API communication with the Supabase project.

    Because Row Level Security (RLS) is enabled and user authentication is not
    yet implemented, unauthorized query responses (HTTP 200 with empty data, or 401/403)
    are recognized as successful communication with the Supabase server.

    Returns:
        (is_connected, details_message)
    """
    url, key = get_supabase_credentials()

    if not url or not key:
        return False, (
            "Credentials not configured. Set SUPABASE_URL and SUPABASE_KEY in "
            ".streamlit/secrets.toml or .env."
        )

    try:
        client = create_client(url, key)

        # Safe probe: query the expenses table.
        # With RLS enabled and no active session, PostgREST responds normally without data leak.
        client.table("expenses").select("id").limit(1).execute()

        return True, "Successfully connected to Supabase project. Table endpoint responded."

    except Exception as exc:
        err_msg = str(exc)
        # Check network resolution errors
        if (
            "Failed to resolve" in err_msg
            or "Name or service not known" in err_msg
            or "getaddrinfo failed" in err_msg
        ):
            return False, "Network error: Unable to resolve Supabase project URL."

        if "Connection refused" in err_msg:
            return False, "Network error: Connection refused by Supabase host."

        if "Invalid API key" in err_msg or "JWSError" in err_msg:
            return False, "Authentication error: The provided Supabase anon key is invalid."

        if 'relation "public.expenses" does not exist' in err_msg:
            return True, (
                "Connected to Supabase project successfully. Note: 'expenses' table has not "
                "been created yet. Run schema.sql in the Supabase SQL Editor."
            )

        # If server responded with an API status, the connection is active
        return True, f"Connected to Supabase project (Server response: {err_msg})"

