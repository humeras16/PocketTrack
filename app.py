import os
import csv
import calendar
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ==========================================
# PAGE SETTINGS
# ==========================================

st.set_page_config(
    page_title="PocketTrack | Expense Dashboard",
    page_icon="💰",
    layout="wide"
)


# ==========================================
# COLOURS  (pastel green palette)
# ==========================================

BG = "#F3FAF1"          # very light mint cream
SIDEBAR = "#DFF3E3"     # soft green
CARD = "#FFFFFF"        # white cards
BORDER = "#BFE5CB"      # green border
GREEN = "#7BCB98"       # main pastel green
DEEP_GREEN = "#3E9A6A"  # darker green for headings
SOFT_GREEN = "#DFF5E6"  # very soft green fill
SKY = "#BBD9F0"
BUTTER = "#FFF1A8"
PEACH = "#FFD3B6"
MINT = "#A8E6CF"
LAVENDER = "#D9CCFF"
TEXT = "#3F5247"        # deep green-grey text
MUTED = "#7B8F83"       # soft grey-green

CATEGORIES = [
    "Food",
    "Travel",
    "Shopping",
    "Education",
    "Bills",
    "Entertainment",
    "Health",
    "Other"
]

# Spending ranges for the daily ring.
# Each item is (label, upper limit, colour).
# The last range has no upper limit (None).
SPEND_BUCKETS = [
    ("0", 0, "#EEF3EE"),
    ("1-20", 20, "#DDF3E4"),
    ("21-40", 40, "#BDE8CB"),
    ("41-60", 60, "#9DDDB3"),
    ("61-80", 80, "#7BCB98"),
    ("81-100", 100, "#5DB880"),
    ("101-150", 150, "#3F9F68"),
    ("151+", None, "#2D7F52")
]


# ==========================================
# CUSTOM DESIGN  (pastel green theme)
# ==========================================

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@400;500;600&family=Nunito:wght@400;600;700&family=Pixelify+Sans:wght@400;600&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Nunito', sans-serif;
    }}

    .stApp {{
        background-color: {BG};
        background-image: radial-gradient(#DCEFE0 2px, transparent 2px);
        background-size: 28px 28px;
        color: {TEXT};
        font-family: 'Nunito', sans-serif;
    }}

    [data-testid="stSidebar"] {{
        background: {SIDEBAR};
        border-right: 3px dashed {GREEN};
    }}

    [data-testid="stSidebar"] * {{
        color: {TEXT};
    }}

    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{
        font-family: 'Pixelify Sans', 'Fredoka', sans-serif;
        font-size: 18px;
        font-weight: 600;
        letter-spacing: 2px;
        color: {DEEP_GREEN};
    }}

    [data-testid="stSidebar"] [role="radiogroup"] label p {{
        font-family: 'Fredoka', sans-serif;
        font-size: 18px;
        font-weight: 500;
        color: {TEXT};
    }}

    [data-testid="stSidebar"] [role="radiogroup"] label {{
        padding: 4px 0;
    }}

    .block-container {{
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }}

    h1, h2, h3 {{
        font-family: 'Pixelify Sans', 'Fredoka', sans-serif !important;
        color: {DEEP_GREEN} !important;
        font-weight: 600 !important;
    }}

    h1 {{
        font-size: 40px !important;
    }}

    p, label {{
        color: {MUTED};
        font-family: 'Nunito', sans-serif;
    }}

    [data-testid="stMetric"] {{
        background: {CARD};
        border: 2px solid {BORDER};
        border-radius: 22px;
        box-shadow: 0 6px 0 rgba(123, 203, 152, 0.30);
        padding: 20px;
    }}

    [data-testid="stHorizontalBlock"] > div:nth-child(1) [data-testid="stMetric"] {{
        background: {SOFT_GREEN};
    }}

    [data-testid="stHorizontalBlock"] > div:nth-child(2) [data-testid="stMetric"] {{
        background: #FFF8DB;
        border-color: #F3E3A3;
        box-shadow: 0 6px 0 rgba(243, 227, 163, 0.60);
    }}

    [data-testid="stHorizontalBlock"] > div:nth-child(3) [data-testid="stMetric"] {{
        background: #E4F1FB;
        border-color: {SKY};
        box-shadow: 0 6px 0 rgba(187, 217, 240, 0.70);
    }}

    [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * {{
        color: {MUTED} !important;
        font-family: 'Nunito', sans-serif !important;
        font-weight: 700 !important;
    }}

    [data-testid="stMetricValue"], [data-testid="stMetricValue"] * {{
        color: {DEEP_GREEN} !important;
        font-family: 'Fredoka', sans-serif !important;
        font-weight: 600 !important;
    }}

    div[data-testid="stPlotlyChart"] {{
        background: {CARD};
        border: 2px solid {BORDER};
        border-radius: 22px;
        box-shadow: 0 6px 0 rgba(123, 203, 152, 0.30);
        padding: 10px;
        overflow: hidden;
    }}

    div[data-testid="stDataFrame"] {{
        border: 2px solid {BORDER};
        border-radius: 18px;
        overflow: hidden;
    }}

    div[data-baseweb="input"],
    div[data-baseweb="base-input"],
    div[data-baseweb="select"] > div {{
        border-radius: 14px !important;
    }}

    .hero {{
        background: linear-gradient(120deg, #D5F2DF, #E4F1FB, #FFF3D1);
        border: 3px solid #FFFFFF;
        border-radius: 28px;
        box-shadow: 0 8px 0 rgba(123, 203, 152, 0.35);
        padding: 30px;
        margin-bottom: 28px;
    }}

    .hero-label {{
        color: {DEEP_GREEN};
        font-family: 'Fredoka', sans-serif;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 2px;
    }}

    .hero-title {{
        color: {TEXT};
        font-family: 'Pixelify Sans', 'Fredoka', sans-serif;
        font-size: 40px;
        font-weight: 600;
        margin-top: 8px;
        margin-bottom: 8px;
    }}

    .hero-text {{
        color: {TEXT};
        font-family: 'Nunito', sans-serif;
        font-size: 16px;
        font-weight: 600;
    }}

    .section-heading {{
        color: {DEEP_GREEN};
        font-family: 'Fredoka', sans-serif;
        font-size: 23px;
        font-weight: 600;
        margin-top: 28px;
        margin-bottom: 4px;
    }}

    .section-subtitle {{
        color: {MUTED};
        font-size: 14px;
        margin-bottom: 15px;
    }}

    .brand {{
        font-family: 'Pixelify Sans', 'Fredoka', sans-serif;
        font-size: 28px;
        font-weight: 600;
        color: {DEEP_GREEN};
        padding: 10px 0 0 0;
    }}

    .brand-subtitle {{
        font-size: 13px;
        color: {MUTED};
        margin-bottom: 25px;
    }}

    .note-card {{
        background: {CARD};
        border: 2px solid {BORDER};
        border-left: 8px solid {SKY};
        border-radius: 22px;
        box-shadow: 0 6px 0 rgba(187, 217, 240, 0.50);
        padding: 18px 22px;
        margin-top: 20px;
    }}

    .note-title {{
        color: {DEEP_GREEN};
        font-family: 'Fredoka', sans-serif;
        font-size: 17px;
        font-weight: 600;
        margin-bottom: 5px;
    }}

    .note-text {{
        color: {TEXT};
        font-size: 14px;
    }}

    .ring-legend {{
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 10px 22px;
        margin-top: 16px;
        margin-bottom: 6px;
    }}

    .ring-item {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        color: {TEXT};
        font-family: 'Nunito', sans-serif;
        font-size: 14px;
        font-weight: 700;
    }}

    .ring-box {{
        display: inline-block;
        width: 20px;
        height: 20px;
        border-radius: 6px;
        border: 2px solid {BORDER};
    }}

    .footer {{
        text-align: center;
        color: {MUTED};
        font-size: 13px;
        padding-top: 40px;
    }}

    div.stButton > button,
    div[data-testid="stFormSubmitButton"] > button {{
        background-color: {GREEN};
        color: #FFFFFF;
        border: none;
        border-radius: 999px;
        box-shadow: 0 5px 0 {DEEP_GREEN};
        font-family: 'Fredoka', sans-serif;
        font-weight: 600;
        font-size: 16px;
        padding: 10px 22px;
    }}

    div.stButton > button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {{
        background-color: #93D8AB;
        color: #FFFFFF;
        border: none;
    }}

    div.stButton > button:active,
    div[data-testid="stFormSubmitButton"] > button:active {{
        box-shadow: 0 0 0 {DEEP_GREEN};
        transform: translateY(5px);
    }}

    </style>
    """,
    unsafe_allow_html=True
)


# ==========================================
# FILE LOCATION
# ==========================================

DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "expenses.txt"
)


# ==========================================
# LOAD EXPENSES
# ==========================================

def load_expenses():

    records = []

    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(
            columns=["Name", "Amount", "Date", "Category"]
        )

    with open(DATA_FILE, "r", encoding="utf-8") as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            try:

                # Read newly saved CSV records and
                # older records with two or three fields.

                if line.startswith('"'):

                    parts = next(csv.reader([line]))

                else:

                    parts = line.rsplit(",", 3)

                    if len(parts) == 4:

                        try:
                            datetime.strptime(
                                parts[2].strip(),
                                "%d-%m-%Y"
                            )

                        except ValueError:

                            parts = line.rsplit(",", 2)

                if len(parts) == 4:

                    name, amount, date_text, category = parts

                    date_value = datetime.strptime(
                        date_text.strip(),
                        "%d-%m-%Y"
                    ).date()

                elif len(parts) == 3:

                    name, amount, date_text = parts

                    date_value = datetime.strptime(
                        date_text.strip(),
                        "%d-%m-%Y"
                    ).date()

                    category = "Uncategorized"

                elif len(parts) == 2:

                    name, amount = parts

                    date_value = None
                    category = "Uncategorized"

                else:
                    continue

                amount = float(amount.strip())
                name = name.strip()

                if name and amount >= 0:

                    records.append({
                        "Name": name,
                        "Amount": amount,
                        "Date": date_value,
                        "Category": category.strip()
                    })

            except (ValueError, TypeError, csv.Error):
                continue

    df = pd.DataFrame(
        records,
        columns=["Name", "Amount", "Date", "Category"]
    )

    if not df.empty:

        df["Date"] = pd.to_datetime(
            df["Date"],
            errors="coerce"
        )

    return df


# Load saved expenses
df = load_expenses()


# ==========================================
# CALCULATIONS
# ==========================================

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
        dated_df["MonthKey"] == current_month,
        "Amount"
    ].sum()

else:

    monthly_df = pd.DataFrame(
        columns=["MonthKey", "Amount", "Month"]
    )

    current_month_spending = 0


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
        gridcolor="#E3F3E8",
        zeroline=False,
        tickfont=dict(color=TEXT, size=12),
        title_font=dict(color=MUTED, size=14)
    )

    return fig


# ==========================================
# MONTHLY LINE GRAPH
# ==========================================

def show_monthly_chart():

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
            "<b>%{x}</b><br>"
            "Spent: ₹%{y:,.2f}"
            "<extra></extra>"
        )
    )

    fig.update_yaxes(rangemode="tozero")

    # A little space on the left and right so labels are not cut off
    fig.update_xaxes(range=[-0.3, len(monthly_df) - 0.7])

    fig = chart_layout(fig, height=400)

    # No axis titles (the heading already explains the chart).
    # Add the rupee sign to the numbers on the side instead.
    fig.update_xaxes(title_text=None, automargin=True)

    fig.update_yaxes(
        title_text=None,
        tickprefix="₹",
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

def bucket_for(amount):

    # Returns the position of the spending range
    # in SPEND_BUCKETS for one day's total.

    if amount <= 0:
        return 0

    for index in range(1, len(SPEND_BUCKETS) - 1):

        upper_limit = SPEND_BUCKETS[index][1]

        if amount <= upper_limit:
            return index

    return len(SPEND_BUCKETS) - 1


def show_spending_ring():

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

    if dated_df.empty:

        st.info(
            "Your spending ring will appear when you have "
            "expenses with dates."
        )

        return

    # ---- Month picker ----

    periods = sorted(
        set(dated_df["MonthKey"]) | {current_month},
        reverse=True
    )

    month_labels = [
        period.strftime("%B %Y") for period in periods
    ]

    latest_index = periods.index(dated_df["MonthKey"].max())

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

    month_data = dated_df[dated_df["MonthKey"] == chosen_period]

    daily_totals = (
        month_data.groupby(month_data["Date"].dt.day)["Amount"]
        .sum()
        .to_dict()
    )

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
            range_text = f"Range: ₹{SPEND_BUCKETS[bucket_id][0]}"

        hover_data.append(
            [day, f"₹{amount:,.2f}", range_text]
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
                    f"<b>₹{month_total:,.0f}</b><br>"
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
            f"Biggest day: {biggest_day} (₹{biggest_amount:,.2f}). "
            "Expenses without a date are not shown here."
        )


# ==========================================
# CATEGORY-WISE EXPENSE BREAKDOWN
# (not used right now, kept so we can bring it back later)
# ==========================================

def show_expense_breakdown():

    st.markdown(
        '<div class="section-heading">Where Your Money Goes 🍰</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">'
        'See how your spending is divided across categories.'
        '</div>',
        unsafe_allow_html=True
    )

    if df.empty:

        st.info("Add some expenses to see your breakdown.")

        return

    breakdown = (
        df.groupby("Category", as_index=False)["Amount"]
        .sum()
        .sort_values("Amount", ascending=False)
    )

    fig = px.pie(
        breakdown,
        names="Category",
        values="Amount",
        hole=0.6,
        color_discrete_sequence=[
            GREEN,
            SKY,
            BUTTER,
            PEACH,
            LAVENDER,
            MINT,
            "#8EC5FF",
            "#B5EAD7",
            "#E2C6FF"
        ]
    )

    fig.update_traces(
        textposition="outside",
        textinfo="percent",
        textfont=dict(
            family="Nunito, sans-serif",
            size=14,
            color=TEXT
        ),

        hovertemplate=(
            "<b>%{label}</b><br>"
            "Amount: ₹%{value:,.2f}<br>"
            "Share: %{percent}"
            "<extra></extra>"
        ),

        marker=dict(
            line=dict(color="#FFFFFF", width=3)
        )
    )

    fig.update_layout(showlegend=True)

    fig = chart_layout(fig, height=430)

    st.plotly_chart(
        fig,
        use_container_width=True,
        theme=None,
        config={"displayModeBar": False}
    )


# ==========================================
# RECENT TRANSACTIONS
# ==========================================

def show_recent_transactions():

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

    if df.empty:

        st.info("No expenses recorded yet.")

        return

    recent = df.copy()

    recent["_sort_date"] = pd.to_datetime(
        recent["Date"],
        errors="coerce"
    )

    recent = recent.sort_values(
        "_sort_date",
        ascending=False,
        na_position="last"
    ).head(8)

    display_df = recent[
        ["Name", "Amount", "Category", "Date"]
    ].copy()

    display_df["Date"] = display_df["Date"].apply(
        lambda value: value.strftime("%d %b %Y")
        if pd.notna(value)
        else "Date not recorded"
    )

    display_df["Amount"] = display_df["Amount"].map(
        lambda value: f"₹{value:,.2f}"
    )

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

    with st.form("add_expense_form"):

        expense_name = st.text_input(
            "Expense Name",
            placeholder="Example: Lunch, Books, Bus ticket"
        )

        col1, col2 = st.columns(2)

        with col1:

            expense_amount = st.number_input(
                "Amount (₹)",
                min_value=0.01,
                value=100.0,
                step=10.0
            )

        with col2:

            expense_category = st.selectbox(
                "Category",
                CATEGORIES
            )

        expense_date = st.date_input(
            "Expense Date",
            value=datetime.today().date()
        )

        submitted = st.form_submit_button(
            "＋ Add Expense",
            use_container_width=True
        )

        if submitted:

            if not expense_name.strip():

                st.error("Please enter an expense name.")

            elif expense_amount <= 0:

                st.error("Please enter an amount greater than zero.")

            else:

                new_record = [
                    expense_name.strip(),
                    expense_amount,
                    expense_date.strftime("%d-%m-%Y"),
                    expense_category
                ]

                try:

                    with open(
                        DATA_FILE,
                        "a",
                        newline="",
                        encoding="utf-8"
                    ) as file:

                        writer = csv.writer(file)
                        writer.writerow(new_record)

                    st.success("Expense added successfully! 💚")

                    st.rerun()

                except OSError:

                    st.error(
                        "Could not save the expense. "
                        "Please check the file location."
                    )

    st.markdown(
        """
        <div class="note-card">
            <div class="note-title">Quick reminder 🌱</div>
            <div class="note-text">
                Every transaction you add is saved in your
                PocketTrack expense file.
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
        f"₹{total_spent:,.2f}"
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
            f"₹{total_spent:,.2f}"
        )

    with col2:

        st.metric(
            "This Month",
            f"₹{current_month_spending:,.2f}"
        )

    with col3:

        st.metric(
            "Transactions",
            f"{transaction_count:,}"
        )

    show_monthly_chart()

    show_spending_ring()

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
            f"₹{total_spent:,.2f}"
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

        display_df = df[
            ["Name", "Amount", "Category", "Date"]
        ].copy()

        display_df["Date"] = display_df["Date"].apply(
            lambda value: value.strftime("%d %b %Y")
            if pd.notna(value)
            else "Date not recorded"
        )

        display_df["Amount"] = display_df["Amount"].map(
            lambda value: f"₹{value:,.2f}"
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

    st.caption(
        "Your transactions are stored in expenses.txt."
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
            f"₹{current_month_spending:,.2f}"
        )

    with col2:

        st.metric(
            "Months Recorded",
            f"{len(monthly_df):,}"
        )

    show_monthly_chart()

    show_spending_ring()

    if not monthly_df.empty:

        st.markdown(
            '<div class="section-heading">Monthly Totals</div>',
            unsafe_allow_html=True
        )

        report_df = monthly_df[
            ["MonthKey", "Month", "Amount"]
        ].copy()

        report_df = report_df.sort_values(
            "MonthKey",
            ascending=False
        )

        report_df["Amount"] = report_df["Amount"].map(
            lambda value: f"₹{value:,.2f}"
        )

        report_df = report_df[
            ["Month", "Amount"]
        ]

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