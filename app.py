
import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st


# PAGE SETTINGS
st.set_page_config(
    page_title="PocketTrack | Expense Dashboard",
    page_icon="💸",
    layout="wide"
)

# COLOURS
BG = "#0B0F12"
SIDEBAR = "#10171B"
CARD = "#131C20"
BORDER = "#26373D"
TEAL = "#55C6AE"
BRIGHT_TEAL = "#83E2CD"
TEXT = "#F2F7F6"
MUTED = "#94A6A8"

# CUSTOM DESIGN
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    .stApp {{
        background: {BG};
        color: {TEXT};
    }}

    [data-testid="stSidebar"] {{
        background: {SIDEBAR};
        border-right: 1px solid {BORDER};
    }}

    [data-testid="stSidebar"] * {{
        color: {TEXT};
    }}

    .block-container {{
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }}

    h1, h2, h3 {{
        color: {TEXT} !important;
        font-weight: 700 !important;
    }}

    p, label {{
        color: {MUTED};
    }}

    [data-testid="stMetric"] {{
        background: {CARD};
        border: 1px solid {BORDER};
        padding: 20px;
        border-radius: 16px;
    }}

    [data-testid="stMetricLabel"] {{
        color: {MUTED} !important;
    }}

    [data-testid="stMetricValue"] {{
        color: {BRIGHT_TEAL} !important;
    }}

    div[data-testid="stPlotlyChart"] {{
        background: {CARD};
        border: 1px solid {BORDER};
        border-radius: 16px;
        padding: 10px;
    }}

    .hero {{
        background: linear-gradient(120deg, #14252A, #11191D);
        border: 1px solid #29443F;
        border-radius: 20px;
        padding: 30px;
        margin-bottom: 25px;
    }}

    .hero-label {{
        color: {TEAL};
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 2px;
    }}

    .hero-title {{
        color: {TEXT};
        font-size: 34px;
        font-weight: 800;
        margin-top: 8px;
        margin-bottom: 8px;
    }}

    .hero-text {{
        color: {MUTED};
        font-size: 15px;
    }}

    .section-heading {{
        color: {TEXT};
        font-size: 21px;
        font-weight: 700;
        margin-top: 20px;
        margin-bottom: 4px;
    }}

    .section-subtitle {{
        color: {MUTED};
        font-size: 13px;
        margin-bottom: 15px;
    }}

    .brand {{
        font-size: 25px;
        font-weight: 800;
        color: {BRIGHT_TEAL};
        padding: 10px 0 0 0;
    }}

    .brand-subtitle {{
        font-size: 12px;
        color: {MUTED};
        margin-bottom: 25px;
    }}

    .note-card {{
        background: {CARD};
        border: 1px solid {BORDER};
        border-left: 4px solid {TEAL};
        border-radius: 14px;
        padding: 18px 20px;
        margin-top: 15px;
    }}

    .note-title {{
        color: {BRIGHT_TEAL};
        font-size: 15px;
        font-weight: 700;
        margin-bottom: 5px;
    }}

    .note-text {{
        color: {MUTED};
        font-size: 13px;
    }}

    .footer {{
        text-align: center;
        color: {MUTED};
        font-size: 12px;
        padding-top: 35px;
    }}
    </style>
    """,
    unsafe_allow_html=True
)


# FILE LOCATION
DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "expenses.txt"
)


# LOAD EXPENSES
def load_expenses():
    records = []

    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(
            columns=["Name", "Amount", "Date"]
        )

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            parts = line.rsplit(",", 2)

            try:
                if len(parts) == 3:
                    name, amount, date_text = parts
                    date_value = datetime.strptime(
                        date_text.strip(), "%d-%m-%Y"
                    ).date()

                elif len(parts) == 2:
                    name, amount = parts
                    date_value = None

                else:
                    continue

                amount = float(amount.strip())
                name = name.strip()

                if name and amount >= 0:
                    records.append({
                        "Name": name,
                        "Amount": amount,
                        "Date": date_value
                    })

            except (ValueError, TypeError):
                continue

    df = pd.DataFrame(records)

    if not df.empty:
        df["Date"] = pd.to_datetime(
            df["Date"], errors="coerce"
        )

    return df


df = load_expenses()


# CALCULATIONS
today = pd.Timestamp.today().normalize()
current_month = today.to_period("M")

total_spent = df["Amount"].sum() if not df.empty else 0
transaction_count = len(df)

dated_df = df.dropna(subset=["Date"]).copy()

if not dated_df.empty:
    dated_df["MonthKey"] = dated_df["Date"].dt.to_period("M")

    monthly_df = (
        dated_df.groupby("MonthKey", as_index=False)["Amount"]
        .sum()
        .sort_values("MonthKey")
    )

    monthly_df["Month"] = monthly_df["MonthKey"].dt.strftime(
        "%b %Y"
    )

    current_month_spending = dated_df.loc[
        dated_df["MonthKey"] == current_month, "Amount"
    ].sum()

else:
    monthly_df = pd.DataFrame(
        columns=["MonthKey", "Amount", "Month"]
    )
    current_month_spending = 0


# CHART STYLE
def chart_layout(fig, height=380):
    fig.update_layout(
        height=height,
        paper_bgcolor=CARD,
        plot_bgcolor=CARD,
        font=dict(
            family="Inter, sans-serif",
            color=TEXT,
            size=12
        ),
        margin=dict(l=20, r=20, t=35, b=20),
        hoverlabel=dict(
            bgcolor="#172328",
            font_color=TEXT
        )
    )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        color=MUTED
    )

    fig.update_yaxes(
        gridcolor=BORDER,
        zeroline=False,
        color=MUTED
    )

    return fig


# MONTHLY LINE GRAPH
def show_monthly_chart():
    st.markdown(
        '<div class="section-heading">Monthly Spending Trend</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">'
        'Follow how your spending changes month by month.'
        '</div>',
        unsafe_allow_html=True
    )

    if monthly_df.empty:
        st.info(
            "Your monthly line graph will appear when you have "
            "expenses with dates. Older undated expenses still "
            "count toward your overall spending."
        )
        return

    fig = px.line(
        monthly_df,
        x="Month",
        y="Amount",
        markers=True,
        labels={
            "Month": "Month",
            "Amount": "Amount spent"
        }
    )

    fig.update_traces(
        line=dict(color=TEAL, width=3),
        marker=dict(
            color=BRIGHT_TEAL,
            size=9,
            line=dict(color=CARD, width=2)
        ),
        fill="tozeroy",
        fillcolor="rgba(85,198,174,0.10)",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Spent: %{y:,.2f}"
            "<extra></extra>"
        )
    )

    fig.update_yaxes(rangemode="tozero")

    fig = chart_layout(fig, height=400)

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False}
    )

    st.caption(
        "Hover over a point to see monthly spending."
    )


# CIRCULAR EXPENSE BREAKDOWN
def show_expense_breakdown():
    st.markdown(
        '<div class="section-heading">Where Your Money Goes</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">'
        'See which expenses make up your spending.'
        '</div>',
        unsafe_allow_html=True
    )

    if df.empty:
        st.info("Add some expenses to see your breakdown.")
        return

    breakdown = (
        df.groupby("Name", as_index=False)["Amount"]
        .sum()
        .sort_values("Amount", ascending=False)
    )

    if len(breakdown) > 7:
        main_categories = breakdown.head(6).copy()
        other_amount = breakdown.iloc[6:]["Amount"].sum()

        breakdown = pd.concat(
            [
                main_categories,
                pd.DataFrame([{
                    "Name": "Other expenses",
                    "Amount": other_amount
                }])
            ],
            ignore_index=True
        )

    fig = px.pie(
        breakdown,
        names="Name",
        values="Amount",
        hole=0.68,
        color_discrete_sequence=[
            "#55C6AE",
            "#83E2CD",
            "#398F81",
            "#B3E8DC",
            "#547B78",
            "#A3B9B6",
            "#6D8C9A"
        ]
    )

    fig.update_traces(
        textposition="outside",
        textinfo="percent",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Amount: %{value:,.2f}<br>"
            "Share: %{percent}"
            "<extra></extra>"
        ),
        marker=dict(
            line=dict(color=CARD, width=3)
        )
    )

    fig.update_layout(showlegend=True)

    fig = chart_layout(fig, height=430)

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False}
    )


# RECENT TRANSACTIONS
def show_recent_transactions():
    st.markdown(
        '<div class="section-heading">Recent Transactions</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">'
        'A quick look at your latest recorded expenses.'
        '</div>',
        unsafe_allow_html=True
    )

    if df.empty:
        st.info("No expenses recorded yet.")
        return

    recent = df.copy()
    recent["_sort_date"] = pd.to_datetime(
        recent["Date"], errors="coerce"
    )

    recent = recent.sort_values(
        "_sort_date",
        ascending=False,
        na_position="last"
    ).head(8)

    display_df = recent[["Name", "Amount", "Date"]].copy()

    display_df["Date"] = display_df["Date"].apply(
        lambda value: value.strftime("%d %b %Y")
        if pd.notna(value) else "Date not recorded"
    )

    display_df["Amount"] = display_df["Amount"].map(
        lambda value: f"{value:,.2f}"
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


# SIDEBAR
with st.sidebar:
    st.markdown(
        """
        <div class="brand">◈ PocketTrack</div>
        <div class="brand-subtitle">Your money, in perspective.</div>
        """,
        unsafe_allow_html=True
    )

    page = st.radio(
        "NAVIGATION",
        ["Dashboard", "Expenses", "Monthly Report"]
    )

    st.markdown("---")
    st.caption("YOUR FINANCIAL SNAPSHOT")

    st.metric("Total spending", f"{total_spent:,.2f}")
    st.caption(f"{transaction_count} transaction(s) recorded")


# DASHBOARD PAGE
if page == "Dashboard":

    st.markdown(
        """
        <div class="hero">
            <div class="hero-label">YOUR PERSONAL FINANCE SPACE</div>
            <div class="hero-title">Welcome to PocketTrack 💸</div>
            <div class="hero-text">
                Small expenses add up. Keep an eye on your money
                and make every rupee count.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Spent", f"{total_spent:,.2f}")

    with col2:
        st.metric("This Month", f"{current_month_spending:,.2f}")

    with col3:
        st.metric("Transactions", f"{transaction_count:,}")

    # Line graph first
    show_monthly_chart()

    # Circular chart BELOW the line graph
    show_expense_breakdown()

    show_recent_transactions()

    st.markdown(
        """
        <div class="note-card">
            <div class="note-title">A little money check-in 🌱</div>
            <div class="note-text">
                Tracking is about understanding your habits, not
                judging every purchase. Review your spending and
                decide what works for you.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# EXPENSES PAGE
elif page == "Expenses":

    st.title("Your Expenses")
    st.caption("Every recorded transaction, all in one place.")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Spent", f"{total_spent:,.2f}")

    with col2:
        st.metric("Transactions", f"{transaction_count:,}")

    if df.empty:
        st.info("No expenses found. Add expenses using PocketTrack.py.")

    else:
        display_df = df[["Name", "Amount", "Date"]].copy()

        display_df["Date"] = display_df["Date"].apply(
            lambda value: value.strftime("%d %b %Y")
            if pd.notna(value) else "Date not recorded"
        )

        display_df["Amount"] = display_df["Amount"].map(
            lambda value: f"{value:,.2f}"
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

    st.caption(
        "This dashboard reads expenses.txt and does not edit "
        "or delete your records."
    )


# MONTHLY REPORT PAGE
elif page == "Monthly Report":

    st.title("Monthly Report")
    st.caption("Your spending trends, without the guesswork.")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Current Month", f"{current_month_spending:,.2f}")

    with col2:
        st.metric("Months Recorded", f"{len(monthly_df):,}")

    show_monthly_chart()
    show_expense_breakdown()

    if not monthly_df.empty:
        st.markdown(
            '<div class="section-heading">Monthly Totals</div>',
            unsafe_allow_html=True
        )

        report_df = monthly_df[
            ["MonthKey", "Month", "Amount"]
        ].copy()

        report_df = report_df.sort_values(
            "MonthKey", ascending=False
        )

        report_df["Amount"] = report_df["Amount"].map(
            lambda value: f"{value:,.2f}"
        )

        report_df = report_df[["Month", "Amount"]]

        st.dataframe(
            report_df,
            use_container_width=True,
            hide_index=True
        )


# FOOTER
st.markdown(
    """
    <div class="footer">
        POCKETTRACK · Spend mindfully. Track confidently. 💚
    </div>
    """,
    unsafe_allow_html=True
)
