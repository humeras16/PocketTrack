import os
import calendar
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from pockettrack.config import (
    STYLE_FILE,
    CURRENCY_SYMBOL,
    MONTH_FULL_FORMAT,
    CARD,
    BORDER,
    GREEN,
    DEEP_GREEN,
    TEXT,
    MUTED,
    GRID_GREEN,
    CATEGORIES,
    SPEND_BUCKETS,
)
from pockettrack.storage import (
    load_expenses,
    save_expense,
    update_expense,
    delete_expense,
    validate_expense,
)
from pockettrack.calculations import (
    get_current_month,
    calculate_total_spending,
    calculate_transaction_count,
    filter_dated_expenses,
    calculate_monthly_spending,
    calculate_current_month_spending,
    calculate_daily_totals,
    bucket_for,
    format_expenses_for_display,
    format_monthly_report_for_display,
)
from pockettrack.auth import (
    is_authenticated,
    validate_or_refresh_session,
    restore_persisted_session,
    sync_persisted_session,
    render_auth_page,
    render_sidebar_user_badge,
)


# ==========================================
# PAGE SETTINGS
# ==========================================

st.set_page_config(
    page_title="PocketTrack | Expense Dashboard",
    page_icon="💰",
    layout="wide"
)


# ==========================================
# CUSTOM DESIGN (loaded from assets/style.css)
# ==========================================

def load_css(file_path: str) -> None:
    """Load and inject an external CSS file into the Streamlit app."""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            st.markdown(f"<style>\n{file.read()}\n</style>", unsafe_allow_html=True)


load_css(STYLE_FILE)


# ==========================================
# AUTHENTICATION GATEWAY
# ==========================================

# Restore persisted session from browser cookie on refresh/startup if not in state
if not is_authenticated():
    restore_persisted_session()

# Validate or refresh session if already authenticated
if is_authenticated():
    validate_or_refresh_session()

# Synchronize cookie persistence state (writes on login/rotation, clears on logout)
sync_persisted_session()

# Gate unauthenticated users
if not is_authenticated():
    render_auth_page()
    st.markdown(
        """
        <div class="footer">
            made with 💚 · spend mindfully, track confidently ✿
        </div>
        """,
        unsafe_allow_html=True
    )
    st.stop()


# ==========================================
# DATA LOADING & SUMMARY CALCULATIONS
# ==========================================

df = load_expenses()
current_month = get_current_month()
total_spent = calculate_total_spending(df)
transaction_count = calculate_transaction_count(df)
dated_df = filter_dated_expenses(df)
monthly_df = calculate_monthly_spending(dated_df)
current_month_spending = calculate_current_month_spending(dated_df, current_month)


# ==========================================
# CHART STYLE
# ==========================================

def chart_layout(fig, height=380):

    fig.update_layout(
        height=height,
        paper_bgcolor=CARD,
        plot_bgcolor=CARD,

        font=dict(
            family="Nunito, sans-serif",
            color=TEXT,
            size=13
        ),

        margin=dict(l=20, r=20, t=35, b=20),

        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor=GREEN,
            font=dict(
                family="Nunito, sans-serif",
                color=TEXT,
                size=14
            )
        )
    )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor=BORDER,
        tickfont=dict(color=TEXT, size=12),
        title_font=dict(color=MUTED, size=14)
    )

    fig.update_yaxes(
        gridcolor=GRID_GREEN,
        zeroline=False,
        tickfont=dict(color=TEXT, size=12),
        title_font=dict(color=MUTED, size=14)
    )

    return fig


# ==========================================
# MONTHLY LINE GRAPH
# ==========================================

def show_monthly_chart(monthly_data: pd.DataFrame):

    st.markdown(
        '<div class="section-heading">Monthly Spending Trend 📈</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">'
        'Follow how your spending changes month by month.'
        '</div>',
        unsafe_allow_html=True
    )

    if monthly_data.empty:

        st.info(
            "Your monthly line graph will appear when you have "
            "expenses with dates. Older undated expenses still "
            "count toward your overall spending."
        )

        return

    fig = px.line(
        monthly_data,
        x="Month",
        y="Amount",
        markers=True,
        labels={
            "Month": "Month",
            "Amount": "Amount spent"
        }
    )

    fig.update_traces(
        line=dict(color=GREEN, width=4, shape="spline"),

        marker=dict(
            symbol="circle",
            color=DEEP_GREEN,
            size=11,
            line=dict(color="#FFFFFF", width=3)
        ),

        fill="tozeroy",
        fillcolor="rgba(123,203,152,0.18)",

        hovertemplate=(
            f"<b>%{{x}}</b><br>"
            f"Spent: {CURRENCY_SYMBOL}%{{y:,.2f}}"
            "<extra></extra>"
        )
    )

    fig.update_yaxes(rangemode="tozero")

    # A little space on the left and right so labels are not cut off
    fig.update_xaxes(range=[-0.3, len(monthly_data) - 0.7])

    fig = chart_layout(fig, height=400)

    # No axis titles (the heading already explains the chart).
    # Add the rupee sign to the numbers on the side instead.
    fig.update_xaxes(title_text=None, automargin=True)

    fig.update_yaxes(
        title_text=None,
        tickprefix=CURRENCY_SYMBOL,
        tickformat=",",
        automargin=True
    )

    fig.update_layout(margin=dict(l=30, r=40, t=30, b=40))

    st.plotly_chart(
        fig,
        use_container_width=True,
        theme=None,
        config={"displayModeBar": False}
    )

    st.caption(
        "Hover over a point to see monthly spending."
    )


# ==========================================
# DAILY SPENDING RING (bullet journal style)
# ==========================================

def show_spending_ring(dated_data: pd.DataFrame, current_period: pd.Period):

    st.markdown(
        '<div class="section-heading">Daily Spending Ring 🍩</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">'
        'Each little block is one day. The darker the colour, '
        'the more you spent that day.'
        '</div>',
        unsafe_allow_html=True
    )

    if dated_data.empty:

        st.info(
            "Your spending ring will appear when you have "
            "expenses with dates."
        )

        return

    # ---- Month picker ----

    periods = sorted(
        set(dated_data["MonthKey"]) | {current_period},
        reverse=True
    )

    month_labels = [
        period.strftime(MONTH_FULL_FORMAT) for period in periods
    ]

    latest_index = periods.index(dated_data["MonthKey"].max())

    pick_col, _ = st.columns([1, 2])

    with pick_col:

        chosen_label = st.selectbox(
            "Pick a month",
            month_labels,
            index=latest_index,
            key="ring_month"
        )

    chosen_period = periods[month_labels.index(chosen_label)]

    # ---- Total spent on each day of that month ----

    days_in_month = calendar.monthrange(
        chosen_period.year,
        chosen_period.month
    )[1]

    daily_totals = calculate_daily_totals(dated_data, chosen_period)

    day_numbers = list(range(1, days_in_month + 1))

    amounts = [
        float(daily_totals.get(day, 0)) for day in day_numbers
    ]

    bucket_ids = [bucket_for(amount) for amount in amounts]

    colours = [SPEND_BUCKETS[i][2] for i in bucket_ids]

    # ---- Hover text for every block ----

    hover_data = []

    for day, amount, bucket_id in zip(day_numbers, amounts, bucket_ids):

        if bucket_id == 0:
            range_text = "No spending"
        else:
            range_text = f"Range: {CURRENCY_SYMBOL}{SPEND_BUCKETS[bucket_id][0]}"

        hover_data.append(
            [day, f"{CURRENCY_SYMBOL}{amount:,.2f}", range_text]
        )

    # ---- Build the ring ----

    slice_size = 360 / days_in_month

    centers = [
        (day - 0.5) * slice_size for day in day_numbers
    ]

    fig = go.Figure(
        go.Barpolar(
            r=[1] * days_in_month,
            theta=centers,
            width=[slice_size] * days_in_month,
            marker=dict(
                color=colours,
                line=dict(color="#FFFFFF", width=3)
            ),
            customdata=hover_data,
            hovertemplate=(
                "<b>Day %{customdata[0]}</b><br>"
                "%{customdata[1]}<br>"
                "%{customdata[2]}"
                "<extra></extra>"
            )
        )
    )

    fig = chart_layout(fig, height=540)

    month_total = sum(amounts)

    fig.update_layout(
        showlegend=False,
        margin=dict(l=50, r=50, t=50, b=50),

        polar=dict(
            bgcolor=CARD,
            hole=0.5,
            radialaxis=dict(
                visible=False,
                range=[0, 1]
            ),
            angularaxis=dict(
                direction="clockwise",
                rotation=90,
                tickmode="array",
                tickvals=centers,
                ticktext=[str(day) for day in day_numbers],
                tickfont=dict(size=13, color=TEXT),
                showgrid=False,
                showline=False,
                ticks=""
            )
        ),

        annotations=[
            dict(
                text=(
                    "💵<br>"
                    f"<b>{CURRENCY_SYMBOL}{month_total:,.0f}</b><br>"
                    f"{chosen_label}"
                ),
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(
                    family="Fredoka, sans-serif",
                    size=20,
                    color=DEEP_GREEN
                )
            )
        ]
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        theme=None,
        config={"displayModeBar": False}
    )

    # ---- Legend (the little colour boxes) ----

    legend_items = ""

    for label, limit, colour in SPEND_BUCKETS:

        legend_items += (
            '<span class="ring-item">'
            f'<span class="ring-box" style="background:{colour};"></span>'
            f'{label}'
            '</span>'
        )

    st.markdown(
        f'<div class="ring-legend">{legend_items}</div>',
        unsafe_allow_html=True
    )

    # ---- Small summary under the ring ----

    spending_days = sum(1 for amount in amounts if amount > 0)

    if spending_days == 0:

        st.caption("No spending recorded in this month ✨")

    else:

        biggest_amount = max(amounts)
        biggest_day = day_numbers[amounts.index(biggest_amount)]

        st.caption(
            f"{spending_days} spending day(s), "
            f"{days_in_month - spending_days} no-spend day(s). "
            f"Biggest day: {biggest_day} ({CURRENCY_SYMBOL}{biggest_amount:,.2f}). "
            "Expenses without a date are not shown here."
        )


# ==========================================
# RECENT TRANSACTIONS
# ==========================================

def show_recent_transactions(expenses_data: pd.DataFrame):

    st.markdown(
        '<div class="section-heading">Recent Transactions 🧾</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">'
        'A quick look at your latest recorded expenses.'
        '</div>',
        unsafe_allow_html=True
    )

    if expenses_data.empty:

        st.info("No expenses recorded yet.")

        return

    display_df = format_expenses_for_display(expenses_data, limit=8)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# ADD EXPENSE FORM
# ==========================================

def add_expense_page():

    st.title("Add a New Expense 🛍️")

    st.caption(
        "Record your spending and keep everything organised."
    )

    # Show success toast after confirmed successful insertion
    if st.session_state.pop("expense_added_success", False):
        st.toast("Expense added successfully!", icon="💚")

    st.markdown(
        '<div class="section-heading">Transaction Details</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">'
        'Enter the details below to add a new transaction.'
        '</div>',
        unsafe_allow_html=True
    )

    if "expense_form_version" not in st.session_state:
        st.session_state["expense_form_version"] = 0

    ver = st.session_state["expense_form_version"]

    with st.form("add_expense_form", enter_to_submit=False):

        expense_name = st.text_input(
            "Expense Name",
            placeholder="Example: Lunch, Books, Bus ticket",
            key=f"expense_name_{ver}"
        )

        col1, col2 = st.columns(2)

        with col1:

            expense_amount = st.number_input(
                f"Amount ({CURRENCY_SYMBOL})",
                min_value=0.01,
                value=None,
                step=10.0,
                placeholder="0.00",
                key=f"expense_amount_{ver}"
            )

        with col2:

            expense_category = st.selectbox(
                "Category",
                CATEGORIES,
                key=f"expense_category_{ver}"
            )

        expense_date = st.date_input(
            "Expense Date",
            value=datetime.today().date(),
            key=f"expense_date_{ver}"
        )

        submitted = st.form_submit_button(
            "＋ Add Expense",
            use_container_width=True
        )

        if submitted:

            is_valid, validation_error = validate_expense(
                expense_name,
                expense_amount if expense_amount is not None else 0.0
            )

            if not is_valid:

                st.error(validation_error)

            else:

                saved, save_error = save_expense(
                    expense_name,
                    expense_amount,
                    expense_date,
                    expense_category
                )

                if saved:

                    # Reset form fields on confirmed successful insert and show toast
                    st.session_state["expense_form_version"] += 1
                    st.session_state["expense_added_success"] = True

                    st.rerun()

                else:

                    st.error(save_error)

    st.markdown(
        """
        <div class="note-card">
            <div class="note-title">Quick reminder 🌱</div>
            <div class="note-text">
                Every transaction you add is securely saved in your
                private PocketTrack database.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:

    st.markdown(
        """
        <div class="brand">💰 PocketTrack</div>
        <div class="brand-subtitle">
            Your money, in perspective ✿
        </div>
        """,
        unsafe_allow_html=True
    )

    render_sidebar_user_badge()

    page = st.radio(
        "NAVIGATION",
        [
            "Dashboard",
            "Add Expense",
            "Expenses",
            "Monthly Report"
        ]
    )

    st.markdown("---")

    st.caption("YOUR FINANCIAL SNAPSHOT")

    st.metric(
        "Total spending",
        f"{CURRENCY_SYMBOL}{total_spent:,.2f}"
    )

    st.caption(
        f"{transaction_count} transaction(s) recorded"
    )


# ==========================================
# DASHBOARD PAGE
# ==========================================

if page == "Dashboard":

    # NOTE: no blank lines inside the HTML below.
    # A blank line makes Streamlit show the HTML as code.
    st.markdown(
        """
        <div class="hero">
            <div class="hero-label">✿ WALLET CHECK ✿</div>
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

        st.metric(
            "Total Spent",
            f"{CURRENCY_SYMBOL}{total_spent:,.2f}"
        )

    with col2:

        st.metric(
            "This Month",
            f"{CURRENCY_SYMBOL}{current_month_spending:,.2f}"
        )

    with col3:

        st.metric(
            "Transactions",
            f"{transaction_count:,}"
        )

    show_monthly_chart(monthly_df)

    show_spending_ring(dated_df, current_month)

    show_recent_transactions(df)

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


# ==========================================
# ADD EXPENSE PAGE
# ==========================================

elif page == "Add Expense":

    add_expense_page()


# ==========================================
# EXPENSES PAGE
# ==========================================

elif page == "Expenses":

    st.title("Your Expenses 🧸")

    st.caption(
        "Every recorded transaction, all in one place."
    )

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Total Spent",
            f"{CURRENCY_SYMBOL}{total_spent:,.2f}"
        )

    with col2:

        st.metric(
            "Transactions",
            f"{transaction_count:,}"
        )

    if df.empty:

        st.info(
            "No expenses found. Visit Add Expense to get started."
        )

    else:

        display_df = format_expenses_for_display(df)

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

    st.caption(
        "Your transactions are securely saved in your PocketTrack account."
    )


# ==========================================
# MONTHLY REPORT PAGE
# ==========================================

elif page == "Monthly Report":

    st.title("Monthly Report 🌿")

    st.caption(
        "Your spending trends, without the guesswork."
    )

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Current Month",
            f"{CURRENCY_SYMBOL}{current_month_spending:,.2f}"
        )

    with col2:

        st.metric(
            "Months Recorded",
            f"{len(monthly_df):,}"
        )

    show_monthly_chart(monthly_df)

    show_spending_ring(dated_df, current_month)

    if not monthly_df.empty:

        st.markdown(
            '<div class="section-heading">Monthly Totals</div>',
            unsafe_allow_html=True
        )

        report_df = format_monthly_report_for_display(monthly_df)

        st.dataframe(
            report_df,
            use_container_width=True,
            hide_index=True
        )


# ==========================================
# FOOTER
# ==========================================

st.markdown(
    """
    <div class="footer">
        made with 💚 · spend mindfully, track confidently ✿
    </div>
    """,
    unsafe_allow_html=True
)
