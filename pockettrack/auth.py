"""
Authentication module for PocketTrack using Supabase Auth.
Provides isolated session management, login, registration, and logout with
clear user feedback and guidance, supporting secure persistence across browser refreshes.
"""
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
import re
import streamlit as st
from supabase import Client
from streamlit_cookies_controller import CookieController, RemoveEmptyElementContainer

from . import supabase_client

# Name of the browser cookie used strictly for session persistence across refreshes.
# Only the refresh token is stored (never passwords, secrets, or service keys).
AUTH_COOKIE_NAME = "pockettrack_refresh_token"
AUTH_COOKIE_KEY = "pockettrack_cookies"
COOKIE_EXPIRY_DAYS = 30


# ==========================================
# COOKIE CONTROLLER
# ==========================================

def get_cookie_controller() -> CookieController:
    """Return the CookieController instance for managing browser session cookies."""
    return CookieController(key=AUTH_COOKIE_KEY)


def get_persisted_refresh_token() -> Optional[str]:
    """
    Retrieve any persisted refresh token from the browser cookie.
    First inspects st.context.cookies (fastest, available on page load/refresh),
    then falls back to CookieController.
    """
    try:
        # Check native Streamlit request context cookies
        if hasattr(st, "context") and hasattr(st.context, "cookies"):
            token = st.context.cookies.get(AUTH_COOKIE_NAME)
            if token and isinstance(token, str) and token.strip():
                return token.strip()
    except Exception:
        pass

    try:
        controller = get_cookie_controller()
        token = controller.get(AUTH_COOKIE_NAME)
        if token and isinstance(token, str) and token.strip():
            return token.strip()
    except Exception:
        pass

    return None


def persist_session_token(refresh_token: str) -> None:
    """
    Persist the refresh token to the client's browser cookie.
    Cookie is scoped to '/', expires in 30 days, same_site='strict'.
    """
    if not refresh_token:
        return
    try:
        controller = get_cookie_controller()
        expiry = datetime.now() + timedelta(days=COOKIE_EXPIRY_DAYS)
        controller.set(
            name=AUTH_COOKIE_NAME,
            value=refresh_token,
            path="/",
            expires=expiry,
            same_site="strict"
        )
    except Exception:
        pass


def clear_persisted_session_token() -> None:
    """Remove the session cookie from the client's browser."""
    try:
        controller = get_cookie_controller()
        controller.remove(
            name=AUTH_COOKIE_NAME,
            path="/",
            same_site="strict"
        )
    except Exception:
        pass


def sync_persisted_session() -> None:
    """
    Ensure the current session's refresh token is accurately persisted to the browser cookie,
    or cleared if a logout was requested.
    Must be called on active (non-aborted) script runs so the component delta reaches the client.
    """
    try:
        RemoveEmptyElementContainer()
    except Exception:
        pass

    # 1. Handle pending cookie removal (e.g. following logout)
    if st.session_state.get("_pending_cookie_clear"):
        clear_persisted_session_token()
        st.session_state.pop("_pending_cookie_clear", None)
        st.session_state.pop("_cookie_persisted_token", None)
        return

    # 2. If authenticated, ensure the current refresh token is persisted to browser cookie
    if is_authenticated():
        auth_session = st.session_state.get("auth_session", {})
        refresh_token = auth_session.get("refresh_token")
        if refresh_token:
            last_persisted = st.session_state.get("_cookie_persisted_token")
            if last_persisted != refresh_token:
                persist_session_token(refresh_token)
                st.session_state["_cookie_persisted_token"] = refresh_token


# ==========================================
# SESSION & CLIENT ISOLATION
# ==========================================

def get_user_client() -> Client:
    """
    Return a per-session Supabase client scoped to the current user's session.
    Guarantees thread and session isolation between different Streamlit users.
    """
    if "user_supabase_client" not in st.session_state:
        st.session_state["user_supabase_client"] = supabase_client.get_supabase_client()

    client: Client = st.session_state["user_supabase_client"]

    # If the user has an active session, ensure the client is authenticated
    auth_session = st.session_state.get("auth_session")
    if auth_session and auth_session.get("access_token") and auth_session.get("refresh_token"):
        try:
            client.auth.set_session(
                auth_session["access_token"],
                auth_session["refresh_token"]
            )
        except Exception:
            pass

    return client


def is_authenticated() -> bool:
    """Check whether the current Streamlit session has an authenticated user."""
    return bool(
        st.session_state.get("auth_user")
        and st.session_state.get("auth_session")
    )


def get_current_user() -> Optional[Dict[str, Any]]:
    """Return dictionary of current authenticated user details (id, email)."""
    return st.session_state.get("auth_user")


def get_current_user_id() -> Optional[str]:
    """Return the Supabase UUID of the authenticated user, or None."""
    user = get_current_user()
    return user.get("id") if user else None


# ==========================================
# AUTHENTICATION ACTIONS
# ==========================================

def sign_in(email: str, password: str) -> Tuple[bool, str, str]:
    """
    Authenticate an existing user with email and password.

    Returns:
        (success, status_code, message)
    """
    email = email.strip()
    if not email or not password:
        return False, "missing_fields", "Please enter both email and password."

    client = get_user_client()

    try:
        response = client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if not response.user or not response.session:
            return False, "no_session", "Could not start session. Please try again."

        # Store isolated session data in Streamlit's per-user session state
        st.session_state["auth_user"] = {
            "id": response.user.id,
            "email": response.user.email,
        }
        st.session_state["auth_session"] = {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "expires_at": response.session.expires_at,
        }
        st.session_state.pop("_cookie_persisted_token", None)

        # Persist refresh token to browser cookie for refresh resilience
        persist_session_token(response.session.refresh_token)

        # Clear any pending registration notice on successful login
        st.session_state.pop("registration_pending_email", None)

        return True, "authenticated", "Login successful! Welcome back."

    except Exception as exc:
        err_code = getattr(exc, "code", "")
        err_msg = getattr(exc, "message", str(exc)).lower()

        if err_code == "email_not_confirmed" or "email not confirmed" in err_msg:
            return False, "unconfirmed_email", (
                "Your email address hasn't been verified yet. "
                "Please check your inbox for the confirmation email, "
                "verify your account, and then try logging in again."
            )
        elif err_code == "invalid_credentials" or "invalid login credentials" in err_msg:
            return False, "invalid_credentials", "Invalid email or password. Please verify your details and try again."
        elif "rate limit" in err_msg:
            return False, "rate_limit", "Too many login attempts. Please wait a moment and try again."
        else:
            return False, "auth_error", "Unable to log in. Please check your credentials or connection."


def sign_up(email: str, password: str, confirm_password: str) -> Tuple[bool, str, str]:
    """
    Register a new user account with email and password.

    Returns:
        (success, status_code, message)
    """
    email = email.strip()
    if not email:
        return False, "missing_email", "Please enter an email address."

    # Email format validation
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return False, "invalid_email", "Please enter a valid email address."

    if not password:
        return False, "missing_password", "Please enter a password."

    if len(password) < 6:
        return False, "weak_password", "Password must be at least 6 characters long."

    if password != confirm_password:
        return False, "password_mismatch", "Passwords do not match. Please verify."

    client = get_user_client()

    try:
        response = client.auth.sign_up({
            "email": email,
            "password": password
        })

        if not response.user:
            return False, "no_user", "Registration could not be completed. Please try again."

        # Case 1: Email confirmation disabled in Supabase -> automatic login
        if response.session:
            st.session_state["auth_user"] = {
                "id": response.user.id,
                "email": response.user.email,
            }
            st.session_state["auth_session"] = {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_at": response.session.expires_at,
            }
            st.session_state.pop("_cookie_persisted_token", None)
            # Persist refresh token to browser cookie for refresh resilience
            persist_session_token(response.session.refresh_token)
            st.session_state.pop("registration_pending_email", None)
            return True, "authenticated", "Account created successfully! Welcome to PocketTrack."

        # Case 2: Email confirmation enabled -> confirmation email sent
        return True, "confirmation_required", (
            f"Account created successfully! Please check your email (**{email}**) "
            "and click the confirmation link before logging in."
        )

    except Exception as exc:
        err_code = getattr(exc, "code", "")
        err_msg = getattr(exc, "message", str(exc)).lower()

        if err_code == "user_already_exists" or "user already registered" in err_msg or "already been registered" in err_msg:
            return False, "duplicate_user", "An account with this email already exists. Please log in instead."
        elif "password should be at least" in err_msg or err_code == "weak_password":
            return False, "weak_password", "Password must be at least 6 characters long."
        elif "invalid format" in err_msg:
            return False, "invalid_email", "Please enter a valid email address."
        elif "rate limit" in err_msg:
            return False, "rate_limit", "Too many signup attempts. Please wait a moment before trying again."
        else:
            return False, "registration_error", "Unable to create account. Please verify your details and try again."


def resend_confirmation_email(email: str) -> Tuple[bool, str]:
    """
    Safely resend confirmation email using the Supabase client.

    Returns:
        (success, message)
    """
    email = email.strip()
    if not email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return False, "Please enter a valid email address to resend the confirmation link."

    client = get_user_client()

    try:
        client.auth.resend({
            "type": "signup",
            "email": email
        })
        return True, f"A new confirmation link has been sent to **{email}**. Please check your inbox and spam folder."

    except Exception as exc:
        err_msg = getattr(exc, "message", str(exc)).lower()
        if "rate limit" in err_msg:
            return False, "Please wait a moment before requesting another confirmation email."
        return False, "Unable to resend confirmation email right now. Please try again later."


def sign_out() -> None:
    """Log out the current user and safely clear all session credentials."""
    client = st.session_state.get("user_supabase_client")
    if client:
        try:
            client.auth.sign_out()
        except Exception:
            pass

    # Flag for cookie removal on next unauthenticated script run so the delta is delivered
    st.session_state["_pending_cookie_clear"] = True
    clear_persisted_session_token()

    st.session_state.pop("auth_user", None)
    st.session_state.pop("auth_session", None)
    st.session_state.pop("user_supabase_client", None)
    st.session_state.pop("registration_pending_email", None)
    st.session_state.pop("login_unconfirmed_email", None)
    st.session_state.pop("_cookie_persisted_token", None)


def validate_or_refresh_session() -> bool:
    """
    Validate that the current session token is still active.
    If the access token is near expiry, automatically refreshes it using the refresh token.
    Avoids unnecessary network overhead on every Streamlit rerun.

    Returns:
        True if session is valid or successfully refreshed; False if expired.
    """
    if not is_authenticated():
        return False

    auth_session = st.session_state.get("auth_session", {})
    expires_at = auth_session.get("expires_at")
    now = time.time()

    # If token has not expired (with 60-second buffer), session is valid
    if expires_at and now < (expires_at - 60):
        return True

    # Token is expired or expiring soon; attempt automatic token refresh
    refresh_token = auth_session.get("refresh_token")
    if not refresh_token:
        sign_out()
        return False

    client = get_user_client()
    try:
        res = client.auth.refresh_session(refresh_token)
        if res.session and res.user:
            st.session_state["auth_session"] = {
                "access_token": res.session.access_token,
                "refresh_token": res.session.refresh_token,
                "expires_at": res.session.expires_at,
            }
            st.session_state["auth_user"] = {
                "id": res.user.id,
                "email": res.user.email,
            }
            # Keep persisted refresh token in sync with updated rotation
            persist_session_token(res.session.refresh_token)
            return True
    except Exception:
        pass

    # Session is expired and cannot be refreshed
    sign_out()
    return False


def restore_persisted_session() -> bool:
    """
    Restore authenticated user session from a persisted browser cookie if present.
    Called on application startup / page refresh when session state is empty.

    Returns:
        True if session was successfully restored; False otherwise.
    """
    if is_authenticated():
        return True

    persisted_token = get_persisted_refresh_token()
    if not persisted_token:
        return False

    client = get_user_client()
    try:
        res = client.auth.refresh_session(persisted_token)
        if res.session and res.user:
            st.session_state["auth_user"] = {
                "id": res.user.id,
                "email": res.user.email,
            }
            st.session_state["auth_session"] = {
                "access_token": res.session.access_token,
                "refresh_token": res.session.refresh_token,
                "expires_at": res.session.expires_at,
            }
            # Record current active token to avoid redundant writes in sync_persisted_session
            st.session_state["_cookie_persisted_token"] = res.session.refresh_token
            # Save newly rotated refresh token to cookie
            persist_session_token(res.session.refresh_token)
            return True
        else:
            clear_persisted_session_token()
            return False
    except Exception:
        # Invalid or expired refresh token; clear stored token
        clear_persisted_session_token()
        return False


# ==========================================
# AUTH UI COMPONENTS
# ==========================================

def render_auth_page() -> None:
    """Render the login and registration screen matching PocketTrack design language."""
    st.markdown(
        """
        <div class="hero">
            <div class="hero-label">✿ POCKETTRACK ACCOUNT ✿</div>
            <div class="hero-title">Welcome to PocketTrack 💸</div>
            <div class="hero-text">
                Your personal money companion. Sign in to manage your expenses
                or create a new account to get started.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Pre-render state synchronization: safe to update widget state BEFORE instantiation
    if st.session_state.pop("_auth_reset_reg_form", False):
        st.session_state.pop("reg_email_input", None)
        st.session_state.pop("reg_password_input", None)
        st.session_state.pop("reg_confirm_input", None)
        st.session_state.pop("login_password_input", None)
        pending_email = st.session_state.get("registration_pending_email")
        if pending_email:
            st.session_state["login_email_input"] = pending_email

    # Determine default active tab (e.g. after registration, automatically switch to Log In)
    active_tab = st.session_state.get("auth_active_tab", "🔑 Log In")

    tab_login, tab_register = st.tabs(
        ["🔑 Log In", "✨ Create Account"],
        default=active_tab
    )

    # ------------------------------------------
    # TAB 1: LOG IN
    # ------------------------------------------
    with tab_login:
        st.markdown(
            '<div class="section-heading" style="margin-top: 12px;">Sign In</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="section-subtitle">Enter your credentials to access your dashboard.</div>',
            unsafe_allow_html=True
        )

        # Show pending confirmation notice if user just registered
        if "registration_pending_email" in st.session_state:
            pending_email = st.session_state["registration_pending_email"]
            st.success(
                f"🎉 **Account created successfully! Please check your email and click the confirmation link before logging in.**\n\n"
                f"Confirmation link sent to: **{pending_email}**\n\n"
                f"👉 *After verifying your email, enter your password below to access your PocketTrack account.*"
            )

        with st.form("login_form"):
            login_email = st.text_input(
                "Email",
                placeholder="you@example.com",
                key="login_email_input"
            )
            login_password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password_input"
            )
            submitted_login = st.form_submit_button(
                "Log In",
                use_container_width=True
            )

            if submitted_login:
                st.session_state["auth_shared_email"] = login_email.strip()
                success, status_code, message = sign_in(login_email, login_password)

                if success:
                    st.success(message)
                    st.rerun()
                elif status_code == "unconfirmed_email":
                    st.session_state["login_unconfirmed_email"] = login_email.strip()
                    st.warning(message)
                else:
                    st.session_state.pop("login_unconfirmed_email", None)
                    st.error(message)

        # If unconfirmed email condition was detected, offer resend action
        if "login_unconfirmed_email" in st.session_state:
            unconfirmed_email = st.session_state["login_unconfirmed_email"]
            st.markdown(
                '<div style="margin-top: 8px; margin-bottom: 4px; font-size: 14px; font-weight: 600;">'
                'Didn\'t receive the confirmation email?</div>',
                unsafe_allow_html=True
            )
            if st.button("✉️ Resend Confirmation Email", key="resend_btn", use_container_width=True):
                resend_ok, resend_msg = resend_confirmation_email(unconfirmed_email)
                if resend_ok:
                    st.success(resend_msg)
                else:
                    st.error(resend_msg)

    # ------------------------------------------
    # TAB 2: CREATE ACCOUNT
    # ------------------------------------------
    with tab_register:
        st.markdown(
            '<div class="section-heading" style="margin-top: 12px;">Create Account</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="section-subtitle">Set up your account to start tracking expenses securely.</div>',
            unsafe_allow_html=True
        )

        # Show confirmation notice here as well if user switches back to register tab
        if "registration_pending_email" in st.session_state:
            pending_email = st.session_state["registration_pending_email"]
            st.success(
                f"🎉 **Account created successfully! Please check your email and click the confirmation link before logging in.**\n\n"
                f"Confirmation link sent to: **{pending_email}**\n\n"
                f"👉 *After confirming your email, go to the **Log In** tab to access your account.*"
            )

        with st.form("register_form"):
            reg_email = st.text_input(
                "Email",
                placeholder="you@example.com",
                key="reg_email_input"
            )
            reg_password = st.text_input(
                "Password (at least 6 characters)",
                type="password",
                placeholder="Create a password",
                key="reg_password_input"
            )
            reg_confirm = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Re-enter your password",
                key="reg_confirm_input"
            )
            submitted_reg = st.form_submit_button(
                "Create Account",
                use_container_width=True
            )

            if submitted_reg:
                entered_email = reg_email.strip()
                success, status_code, message = sign_up(reg_email, reg_password, reg_confirm)

                if success:
                    # Request form reset on the next rerun before widgets are instantiated
                    st.session_state["_auth_reset_reg_form"] = True

                    if status_code == "confirmation_required":
                        # Record pending email for user guidance and login pre-fill
                        st.session_state["registration_pending_email"] = entered_email
                        st.session_state["auth_shared_email"] = entered_email
                        # Automatically switch to Log In tab
                        st.session_state["auth_active_tab"] = "🔑 Log In"
                        st.session_state.pop("login_unconfirmed_email", None)
                        st.rerun()
                    else:
                        # Email confirmation disabled; immediately logged in
                        st.success(message)
                        st.rerun()
                elif status_code == "duplicate_user":
                    # Keep input fields intact on failure
                    st.session_state["auth_shared_email"] = entered_email
                    st.error(message)
                    st.info("💡 Already have an account? Switch to the **Log In** tab above.")
                else:
                    # Keep input fields intact on validation or network errors
                    st.session_state["auth_shared_email"] = entered_email
                    st.error(message)


def render_sidebar_user_badge() -> None:
    """Render user email badge and logout button in the sidebar."""
    user = get_current_user()
    if not user:
        return

    email_display = user.get("email", "Active User")

    st.markdown(
        f"""
        <div class="note-card" style="margin-top: 10px; margin-bottom: 12px; padding: 12px 14px;">
            <div class="note-title" style="font-size: 13px; margin-bottom: 2px;">Signed in as 👤</div>
            <div class="note-text" style="font-size: 13px; font-weight: 700; word-break: break-all;">
                {email_display}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("🚪 Log Out", use_container_width=True, key="logout_btn"):
        sign_out()
        st.rerun()
