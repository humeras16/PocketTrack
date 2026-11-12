"""
Expense calculations, aggregations, and formatting helpers for PocketTrack.
Decoupled from the Streamlit UI presentation.
"""
import calendar
import pandas as pd

from .config import (
    CURRENCY_SYMBOL,
    DATE_DISPLAY_FORMAT,
    MONTH_DISPLAY_FORMAT,
    SPEND_BUCKETS,
)


def get_current_month() -> pd.Period:
    """Return the current year-month Period (e.g. Period('2026-11', 'M'))."""
    return pd.Timestamp.today().normalize().to_period("M")


def calculate_total_spending(df: pd.DataFrame) -> float:
    """Calculate the sum of all recorded expense amounts."""
    if df.empty:
        return 0.0
    return float(df["Amount"].sum())


def calculate_transaction_count(df: pd.DataFrame) -> int:
    """Return the total number of recorded transactions."""
    return len(df)


def filter_dated_expenses(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a copy of the dataframe containing only rows with valid dates,
    with an added 'MonthKey' Period column for monthly grouping.
    """
    dated = df.dropna(subset=["Date"]).copy()
    if not dated.empty:
        dated["MonthKey"] = dated["Date"].dt.to_period("M")
    else:
        dated["MonthKey"] = pd.Series(dtype="period[M]")
    return dated


def calculate_monthly_spending(dated_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate expenses by month.

    Returns:
        DataFrame with columns: ['MonthKey', 'Amount', 'Month']
        sorted chronologically by MonthKey.
    """
    if dated_df.empty:
        return pd.DataFrame(columns=["MonthKey", "Amount", "Month"])

    temp_df = dated_df
    if "MonthKey" not in temp_df.columns:
        temp_df = temp_df.copy()
        temp_df["MonthKey"] = temp_df["Date"].dt.to_period("M")

    monthly_df = (
        temp_df.groupby("MonthKey", as_index=False)["Amount"]
        .sum()
        .sort_values("MonthKey")
    )
    monthly_df["Month"] = monthly_df["MonthKey"].dt.strftime(
        MONTH_DISPLAY_FORMAT
    )
    return monthly_df


def calculate_current_month_spending(
    dated_df: pd.DataFrame,
    current_month: pd.Period | None = None
) -> float:
    """Calculate total spending for the specified or current month."""
    if dated_df.empty:
        return 0.0

    if current_month is None:
        current_month = get_current_month()

    temp_df = dated_df
    if "MonthKey" not in temp_df.columns:
        temp_df = temp_df.copy()
        temp_df["MonthKey"] = temp_df["Date"].dt.to_period("M")

    matches = temp_df.loc[temp_df["MonthKey"] == current_month, "Amount"]
    if matches.empty:
        return 0.0
    return float(matches.sum())


def calculate_daily_totals(
    dated_df: pd.DataFrame,
    period: pd.Period
) -> dict[int, float]:
    """
    Compute total spent per day of the month for the given Period.

    Returns:
        dict mapping day of month (int) to total amount (float).
    """
    if dated_df.empty:
        return {}

    temp_df = dated_df
    if "MonthKey" not in temp_df.columns:
        temp_df = temp_df.copy()
        temp_df["MonthKey"] = temp_df["Date"].dt.to_period("M")

    month_data = temp_df[temp_df["MonthKey"] == period]
    if month_data.empty:
        return {}

    return (
        month_data.groupby(month_data["Date"].dt.day)["Amount"]
        .sum()
        .to_dict()
    )


def bucket_for(amount: float) -> int:
    """
    Return the index in SPEND_BUCKETS corresponding to one day's spending total.
    """
    if amount <= 0:
        return 0

    for index in range(1, len(SPEND_BUCKETS) - 1):
        upper_limit = SPEND_BUCKETS[index][1]
        if amount <= upper_limit:
            return index

    return len(SPEND_BUCKETS) - 1


def format_expenses_for_display(
    df: pd.DataFrame,
    limit: int | None = None
) -> pd.DataFrame:
    """
    Format expense DataFrame for table display with formatted dates and currency.

    Parameters:
        df: DataFrame containing Name, Amount, Category, Date
        limit: Optional maximum rows to return (sorted descending by Date)

    Returns:
        Formatted DataFrame ready for display.
    """
    if df.empty:
        return df.copy()

    target = df.copy()
    if limit is not None:
        target = target.sort_values(
            "Date",
            ascending=False,
            na_position="last"
        ).head(limit)

    display_df = target[["Name", "Amount", "Category", "Date"]].copy()

    display_df["Date"] = display_df["Date"].apply(
        lambda value: value.strftime(DATE_DISPLAY_FORMAT)
        if pd.notna(value)
        else "Date not recorded"
    )

    display_df["Amount"] = display_df["Amount"].map(
        lambda value: f"{CURRENCY_SYMBOL}{value:,.2f}"
    )

    return display_df


def format_monthly_report_for_display(
    monthly_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Format monthly summary DataFrame for table display.
    Sorts descending by MonthKey, formats amounts as currency strings.
    """
    if monthly_df.empty:
        return pd.DataFrame(columns=["Month", "Amount"])

    report_df = monthly_df[["MonthKey", "Month", "Amount"]].copy()
    report_df = report_df.sort_values("MonthKey", ascending=False)
    report_df["Amount"] = report_df["Amount"].map(
        lambda value: f"{CURRENCY_SYMBOL}{value:,.2f}"
    )
    return report_df[["Month", "Amount"]]

