"""
Data persistence and validation logic for PocketTrack.
Stores and retrieves expense records using Supabase PostgreSQL with Row Level Security (RLS).
Ensures every operation is scoped strictly to the authenticated user's session.
"""
from typing import Optional, Tuple
from datetime import datetime, date
import pandas as pd

from .config import DATE_STORAGE_FORMAT
from .auth import get_user_client, get_current_user_id


def validate_expense(name: str, amount: float) -> Tuple[bool, Optional[str]]:
    """
    Validate expense entry details.

    Returns:
        (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "Please enter an expense name."

    if amount <= 0:
        return False, "Please enter an amount greater than zero."

    return True, None


def load_expenses() -> pd.DataFrame:
    """
    Fetch all expenses belonging to the currently authenticated user from Supabase.
    Returns a pandas DataFrame matching the interface expected by calculations.py and app.py:
        Columns: ["Name", "Amount", "Date", "Category", "id"]
    If the user is not authenticated or the network fails, returns an empty DataFrame
    and does not fall back to shared CSV storage.
    """
    user_id = get_current_user_id()
    if not user_id:
        return pd.DataFrame(columns=["Name", "Amount", "Date", "Category", "id"])

    client = get_user_client()
    try:
        response = (
            client.table("expenses")
            .select("id, name, amount, date, category")
            .order("date", desc=True)
            .execute()
        )

        rows = response.data or []
        records = []
        for row in rows:
            raw_date = row.get("date")
            date_value = None
            if raw_date:
                try:
                    date_value = datetime.strptime(str(raw_date)[:10], "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    date_value = None

            records.append({
                "id": row.get("id"),
                "Name": str(row.get("name") or "").strip(),
                "Amount": float(row.get("amount") or 0.0),
                "Date": date_value,
                "Category": str(row.get("category") or "Uncategorized").strip(),
            })

        df = pd.DataFrame(
            records,
            columns=["Name", "Amount", "Date", "Category", "id"]
        )

        if not df.empty:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        return df

    except Exception:
        # Return empty DataFrame on query failure to guarantee isolation
        return pd.DataFrame(columns=["Name", "Amount", "Date", "Category", "id"])


def save_expense(
    name: str,
    amount: float,
    date_val,
    category: str
) -> Tuple[bool, Optional[str]]:
    """
    Insert a new expense into Supabase associated with the authenticated user.
    Uses the authenticated user UUID from get_current_user_id().

    Returns:
        (success, error_message)
    """
    user_id = get_current_user_id()
    if not user_id:
        return False, "You must be signed in to add an expense."

    # Format date as YYYY-MM-DD for PostgreSQL DATE type
    if isinstance(date_val, (date, datetime)):
        formatted_date = date_val.strftime("%Y-%m-%d")
    elif date_val:
        formatted_date = str(date_val).strip()
    else:
        formatted_date = None

    payload = {
        "user_id": user_id,
        "name": name.strip(),
        "amount": float(amount),
        "date": formatted_date,
        "category": category.strip() if category else "Uncategorized",
    }

    client = get_user_client()
    try:
        response = client.table("expenses").insert(payload).execute()
        if response.data and len(response.data) > 0:
            return True, None
        return True, None
    except Exception as exc:
        err_msg = getattr(exc, "message", str(exc))
        return False, f"Could not save expense to database: {err_msg}"


def update_expense(
    expense_id: str,
    name: str,
    amount: float,
    date_val,
    category: str
) -> Tuple[bool, Optional[str]]:
    """
    Update an existing expense belonging to the authenticated user in Supabase.

    Returns:
        (success, error_message)
    """
    user_id = get_current_user_id()
    if not user_id:
        return False, "You must be signed in to update an expense."

    if isinstance(date_val, (date, datetime)):
        formatted_date = date_val.strftime("%Y-%m-%d")
    elif date_val:
        formatted_date = str(date_val).strip()
    else:
        formatted_date = None

    payload = {
        "name": name.strip(),
        "amount": float(amount),
        "date": formatted_date,
        "category": category.strip() if category else "Uncategorized",
    }

    client = get_user_client()
    try:
        # Strict user_id and expense_id matching
        response = (
            client.table("expenses")
            .update(payload)
            .eq("id", expense_id)
            .eq("user_id", user_id)
            .execute()
        )
        if response.data and len(response.data) > 0:
            return True, None
        return False, "Expense not found or you do not have permission to edit it."
    except Exception as exc:
        err_msg = getattr(exc, "message", str(exc))
        return False, f"Could not update expense: {err_msg}"


def delete_expense(expense_id: str) -> Tuple[bool, Optional[str]]:
    """
    Delete an expense belonging to the authenticated user from Supabase.

    Returns:
        (success, error_message)
    """
    user_id = get_current_user_id()
    if not user_id:
        return False, "You must be signed in to delete an expense."

    client = get_user_client()
    try:
        response = (
            client.table("expenses")
            .delete()
            .eq("id", expense_id)
            .eq("user_id", user_id)
            .execute()
        )
        if response.data and len(response.data) > 0:
            return True, None
        return False, "Expense not found or you do not have permission to delete it."
    except Exception as exc:
        err_msg = getattr(exc, "message", str(exc))
        return False, f"Could not delete expense: {err_msg}"
