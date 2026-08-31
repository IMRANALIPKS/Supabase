# ============================================================
# OD PAKISTAN - COMPLETE STREAMLIT DASHBOARD
# Supabase / PostgreSQL
# ============================================================

import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go
from datetime import date


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="OD PAKISTAN Dashboard",
    page_icon="OD",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Main background */
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(6, 182, 212, 0.14), transparent 30%),
            linear-gradient(135deg, #eef6f7 0%, #f7fafc 46%, #f2f4f8 100%);
        color: #111827;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }

    /* Main title */
    .main-title {
        font-size: clamp(28px, 3vw, 42px);
        font-weight: 800;
        color: #0f172a;
        letter-spacing: 0;
        margin-bottom: 2px;
    }

    .sub-title {
        font-size: 15px;
        color: #475569;
        margin-bottom: 20px;
        font-weight: 500;
    }

    .hero-panel {
        background: linear-gradient(135deg, rgba(255,255,255,0.94), rgba(224,247,250,0.72));
        border: 1px solid rgba(148, 163, 184, 0.28);
        border-radius: 18px;
        padding: 22px 26px;
        margin-bottom: 20px;
        box-shadow:
            0 24px 52px rgba(15, 23, 42, 0.13),
            inset 0 1px 0 rgba(255,255,255,0.85);
    }

    .hero-meta {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 12px;
    }

    .hero-pill {
        background: rgba(255,255,255,0.82);
        border: 1px solid rgba(14, 116, 144, 0.16);
        border-radius: 999px;
        color: #164e63;
        font-size: 12px;
        font-weight: 700;
        padding: 7px 11px;
    }

    /* KPI cards */
    .kpi-card {
        background: linear-gradient(145deg, #ffffff, #edf6f7);
        padding: 18px;
        border-radius: 14px;
        border: 1px solid rgba(148, 163, 184, 0.28);
        box-shadow:
            10px 14px 28px rgba(15, 23, 42, 0.14),
            -6px -6px 18px rgba(255,255,255,0.85),
            inset 0 1px 0 rgba(255,255,255,0.9);
        min-height: 128px;
        transition: transform 0.18s ease, box-shadow 0.18s ease;
    }

    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow:
            13px 18px 34px rgba(15, 23, 42, 0.18),
            -6px -6px 18px rgba(255,255,255,0.9);
    }

    .kpi-title {
        font-size: 14px;
        color: #334155;
        font-weight: 700;
    }

    .kpi-value {
        font-size: clamp(20px, 1.6vw, 27px);
        font-weight: 800;
        color: #0f172a;
        margin-top: 8px;
        line-height: 1.15;
    }

    .kpi-small {
        font-size: 12px;
        color: #64748b;
        margin-top: 5px;
        font-weight: 500;
    }

    /* Section title */
    .section-title {
        font-size: 20px;
        font-weight: 800;
        color: #0f172a;
        margin-top: 24px;
        margin-bottom: 10px;
        letter-spacing: 0;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #164e63 100%);
        box-shadow: 8px 0 26px rgba(15, 23, 42, 0.18);
    }

    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] .stSubheader,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span {
        color: #f8fafc;
    }

    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] textarea {
        color: #0f172a !important;
        font-weight: 600;
    }

    div[data-testid="stVerticalBlock"] > div:has(.stPlotlyChart) {
        background: rgba(255,255,255,0.82);
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 16px;
        padding: 12px;
        box-shadow:
            0 20px 44px rgba(15, 23, 42, 0.10),
            inset 0 1px 0 rgba(255,255,255,0.92);
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 14px;
        overflow: hidden;
        box-shadow: 0 16px 34px rgba(15, 23, 42, 0.10);
    }

    .stButton > button,
    .stDownloadButton > button {
        border-radius: 12px;
        border: 1px solid rgba(14, 116, 144, 0.28);
        background: linear-gradient(145deg, #0891b2, #0f766e);
        color: white;
        font-weight: 800;
        box-shadow: 0 12px 22px rgba(8, 145, 178, 0.24);
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        border-color: rgba(15, 118, 110, 0.45);
        transform: translateY(-1px);
    }

    /* Divider */
    hr {
        margin-top: 10px;
        margin-bottom: 10px;
    }

</style>
""", unsafe_allow_html=True)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    try:

        # ----------------------------------------------------
        # OPTION 1:
        # Streamlit secrets
        # ----------------------------------------------------

        if "DATABASE_URL" in st.secrets:

            return psycopg2.connect(
                st.secrets["DATABASE_URL"]
            )

        # ----------------------------------------------------
        # OPTION 2:
        # Separate database parameters
        # ----------------------------------------------------

        return psycopg2.connect(
            host=st.secrets["DB_HOST"],
            port=st.secrets.get("DB_PORT", 5432),
            database=st.secrets["DB_NAME"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"]
        )

    except Exception as e:

        st.error("Database connection failed.")
        st.code(str(e))

        st.stop()


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data(ttl=60)
def load_data():

    conn = get_connection()

    query = """
        SELECT
            id,
            branch,
            inv_date,
            inv_no,
            description,
            uom,
            quantity,
            rate,
            to_rate,
            amount
        FROM supply_sheet
        ORDER BY inv_date, branch, id
    """

    try:

        df = pd.read_sql_query(query, conn)

    except Exception as e:

        st.error("Unable to load data from supply_sheet.")
        st.code(str(e))
        conn.close()
        st.stop()

    finally:

        conn.close()

    # --------------------------------------------------------
    # Data cleaning
    # --------------------------------------------------------

    if df.empty:
        return df

    df["inv_date"] = pd.to_datetime(
        df["inv_date"],
        errors="coerce"
    )

    numeric_columns = [
        "quantity",
        "rate",
        "to_rate",
        "amount"
    ]

    for col in numeric_columns:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        ).fillna(0)

    df["branch"] = (
        df["branch"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["description"] = (
        df["description"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["uom"] = (
        df["uom"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["inv_no"] = (
        df["inv_no"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # Additional calculated columns
    # --------------------------------------------------------

    df["year"] = df["inv_date"].dt.year

    df["month"] = df["inv_date"].dt.month

    df["month_name"] = df["inv_date"].dt.strftime("%b")

    df["month_year"] = df["inv_date"].dt.strftime("%Y-%m")

    df["day"] = df["inv_date"].dt.day

    df["day_name"] = df["inv_date"].dt.strftime("%A")

    df["rate_difference"] = df["to_rate"] - df["rate"]

    df["rate_difference_amount"] = (
        df["quantity"] *
        df["rate_difference"]
    )

    return df


# ============================================================
# NUMBER FORMAT
# ============================================================

def format_number(value):

    if pd.isna(value):
        return "0"

    return f"{value:,.0f}"


def format_amount(value):

    if pd.isna(value):
        return "0"

    return f"Rs. {value:,.0f}"


def style_plotly_chart(fig):

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0.84)",
        font=dict(
            family="Inter, Segoe UI, sans-serif",
            color="#0f172a",
            size=13
        ),
        title=dict(
            font=dict(
                size=18,
                color="#0f172a",
                family="Inter, Segoe UI, sans-serif"
            ),
            x=0.02,
            xanchor="left"
        ),
        margin=dict(l=20, r=20, t=62, b=34),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(148, 163, 184, 0.22)",
        zeroline=False,
        linecolor="rgba(15, 23, 42, 0.18)",
        title_font=dict(size=13),
        tickfont=dict(size=12)
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(148, 163, 184, 0.22)",
        zeroline=False,
        linecolor="rgba(15, 23, 42, 0.18)",
        title_font=dict(size=13),
        tickfont=dict(size=12)
    )

    for trace in fig.data:
        if getattr(trace, "type", "") == "bar":
            trace.marker.line = dict(color="rgba(255,255,255,0.80)", width=1.2)
        if getattr(trace, "type", "") in {"scatter", "bar"}:
            trace.hoverlabel = dict(
                bgcolor="#0f172a",
                font_size=12,
                font_family="Inter, Segoe UI, sans-serif"
            )

    return fig


_streamlit_plotly_chart = st.plotly_chart


def plotly_chart_3d(fig, *args, **kwargs):

    return _streamlit_plotly_chart(
        style_plotly_chart(fig),
        *args,
        **kwargs
    )


st.plotly_chart = plotly_chart_3d


# ============================================================
# LOAD DATA
# ============================================================

df = load_data()


# ============================================================
# EMPTY DATABASE CHECK
# ============================================================

if df.empty:

    st.title(" OD PAKISTAN Dashboard")

    st.warning(
        "No records were found in the supply_sheet table."
    )

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <h2 style="
            color:white;
            margin-bottom:0px;
        ">
        OD PAKISTAN
        </h2>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <p style="
            color:#9ca3af;
            margin-top:0px;
        ">
        Supply Dashboard
        </p>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    st.subheader("Search & Filters")

    global_search = st.text_input(
        "Search all data",
        placeholder="Branch, invoice, item, UOM, amount..."
    )

    # --------------------------------------------------------
    # Date filter
    # --------------------------------------------------------

    min_date = df["inv_date"].min().date()

    max_date = df["inv_date"].max().date()

    date_range = st.date_input(
        "Invoice Date",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:

        start_date = pd.Timestamp(date_range[0])

        end_date = (
            pd.Timestamp(date_range[1])
            + pd.Timedelta(days=1)
            - pd.Timedelta(seconds=1)
        )

    else:

        start_date = pd.Timestamp(min_date)

        end_date = pd.Timestamp(max_date) + pd.Timedelta(days=1)

    # --------------------------------------------------------
    # Branch
    # --------------------------------------------------------

    branch_options = sorted(
        [x for x in df["branch"].unique() if x]
    )

    selected_branches = st.multiselect(
        "Branch",
        options=branch_options,
        default=branch_options
    )

    # --------------------------------------------------------
    # UOM
    # --------------------------------------------------------

    uom_options = sorted(
        [x for x in df["uom"].unique() if x]
    )

    selected_uom = st.multiselect(
        "UOM",
        options=uom_options,
        default=uom_options
    )

    # --------------------------------------------------------
    # Description
    # --------------------------------------------------------

    description_search = st.text_input(
        "Description Search",
        placeholder="Search item description"
    )

    # --------------------------------------------------------
    # Invoice Search
    # --------------------------------------------------------

    invoice_search = st.text_input(
        "Invoice No Search",
        placeholder="Search invoice number"
    )

    st.divider()

    if st.button(
        "Refresh Database",
        use_container_width=True
    ):

        st.cache_data.clear()

        st.rerun()


# ============================================================
# APPLY FILTERS
# ============================================================

filtered_df = df.copy()


# Date

filtered_df = filtered_df[
    (filtered_df["inv_date"] >= start_date)
    &
    (filtered_df["inv_date"] <= end_date)
]


# Global search

if global_search:

    searchable_columns = [
        "branch",
        "inv_no",
        "description",
        "uom",
        "quantity",
        "rate",
        "to_rate",
        "amount"
    ]

    search_text = global_search.strip()

    search_frame = (
        filtered_df[searchable_columns]
        .astype(str)
        .agg(" ".join, axis=1)
    )

    filtered_df = filtered_df[
        search_frame.str.contains(
            search_text,
            case=False,
            na=False,
            regex=False
        )
    ]


# Branch

if selected_branches:

    filtered_df = filtered_df[
        filtered_df["branch"].isin(
            selected_branches
        )
    ]


# UOM

if selected_uom:

    filtered_df = filtered_df[
        filtered_df["uom"].isin(
            selected_uom
        )
    ]


# Description search

if description_search:

    filtered_df = filtered_df[
        filtered_df["description"]
        .str.contains(
            description_search,
            case=False,
            na=False,
            regex=False
        )
    ]


# Invoice search

if invoice_search:

    filtered_df = filtered_df[
        filtered_df["inv_no"]
        .str.contains(
            invoice_search,
            case=False,
            na=False,
            regex=False
        )
    ]

# ============================================================
# HEADER
# ============================================================

st.markdown(
    f"""
    <div class="hero-panel">
        <div class="main-title">OD PAKISTAN Dashboard</div>
        <div class="sub-title">
            Professional supply, invoice, branch, item, and rate analysis
        </div>
        <div class="hero-meta">
            <span class="hero-pill">{format_number(len(filtered_df))} matching records</span>
            <span class="hero-pill">{format_amount(filtered_df["amount"].sum())} filtered amount</span>
            <span class="hero-pill">Search-ready data table</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)



# ============================================================
# KPI CALCULATIONS
# ============================================================

total_amount = filtered_df["amount"].sum()

total_quantity = filtered_df["quantity"].sum()

total_records = len(filtered_df)

total_invoices = filtered_df["inv_no"].nunique()

total_branches = filtered_df["branch"].nunique()

average_invoice = (
    total_amount / total_invoices
    if total_invoices > 0
    else 0
)


# ============================================================
# KPI CARDS
# ============================================================

k1, k2, k3, k4, k5, k6 = st.columns(6)


with k1:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title"> Total Amount</div>
            <div class="kpi-value">
                Rs. {total_amount:,.0f}
            </div>
            <div class="kpi-small">
                Filtered amount
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with k2:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title"> Quantity</div>
            <div class="kpi-value">
                {total_quantity:,.0f}
            </div>
            <div class="kpi-small">
                Total quantity
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with k3:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title"> Records</div>
            <div class="kpi-value">
                {total_records:,}
            </div>
            <div class="kpi-small">
                Supply records
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with k4:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title"> Invoices</div>
            <div class="kpi-value">
                {total_invoices:,}
            </div>
            <div class="kpi-small">
                Unique invoices
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with k5:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title"> Branches</div>
            <div class="kpi-value">
                {total_branches:,}
            </div>
            <div class="kpi-small">
                Active branches
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with k6:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title"> Avg Invoice</div>
            <div class="kpi-value">
                Rs. {average_invoice:,.0f}
            </div>
            <div class="kpi-small">
                Average amount
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# DATA CHECK
# ============================================================

if filtered_df.empty:

    st.warning(
        "No data matches the selected filters."
    )

    st.stop()


# ============================================================
# DAILY TREND
# ============================================================

st.markdown(
    '<div class="section-title">'
    ' Daily Amount Trend'
    '</div>',
    unsafe_allow_html=True
)

daily = (
    filtered_df
    .groupby("inv_date", as_index=False)
    ["amount"]
    .sum()
    .sort_values("inv_date")
)

fig_daily = px.line(
    daily,
    x="inv_date",
    y="amount",
    markers=True,
    title="Daily Supply Amount"
)

fig_daily.update_layout(
    height=400,
    xaxis_title="Date",
    yaxis_title="Amount",
    hovermode="x unified"
)

fig_daily.update_yaxes(
    tickprefix="Rs. ",
    separatethousands=True
)

st.plotly_chart(
    fig_daily,
    use_container_width=True
)


# ============================================================
# MONTHLY TREND
# ============================================================

col1, col2 = st.columns(2)


with col1:

    st.markdown(
        '<div class="section-title">'
        ' Monthly Amount'
        '</div>',
        unsafe_allow_html=True
    )

    monthly = (
        filtered_df
        .groupby(
            "month_year",
            as_index=False
        )
        ["amount"]
        .sum()
        .sort_values("month_year")
    )

    fig_month = px.line(
        monthly,
        x="month_year",
        y="amount",
        markers=True,
        title="Monthly Amount Trend"
    )

    fig_month.update_layout(
        height=400,
        xaxis_title="Month",
        yaxis_title="Amount"
    )

    fig_month.update_yaxes(
        tickprefix="Rs. ",
        separatethousands=True
    )

    st.plotly_chart(
        fig_month,
        use_container_width=True
    )


# ============================================================
# MONTHLY QUANTITY
# ============================================================

with col2:

    st.markdown(
        '<div class="section-title">'
        ' Monthly Quantity'
        '</div>',
        unsafe_allow_html=True
    )

    monthly_qty = (
        filtered_df
        .groupby(
            "month_year",
            as_index=False
        )
        ["quantity"]
        .sum()
        .sort_values("month_year")
    )

    fig_month_qty = px.bar(
        monthly_qty,
        x="month_year",
        y="quantity",
        title="Monthly Quantity"
    )

    fig_month_qty.update_layout(
        height=400,
        xaxis_title="Month",
        yaxis_title="Quantity"
    )

    st.plotly_chart(
        fig_month_qty,
        use_container_width=True
    )


# ============================================================
# BRANCH ANALYSIS
# ============================================================

branch_summary = (
    filtered_df
    .groupby("branch", as_index=False)
    .agg(
        amount=("amount", "sum"),
        quantity=("quantity", "sum"),
        invoices=("inv_no", "nunique")
    )
    .sort_values(
        "amount",
        ascending=False
    )
)


col1, col2 = st.columns(2)


# ============================================================
# BRANCH AMOUNT
# ============================================================

with col1:

    st.markdown(
        '<div class="section-title">'
        ' Branch-wise Amount'
        '</div>',
        unsafe_allow_html=True
    )

    fig_branch = px.bar(
        branch_summary,
        x="branch",
        y="amount",
        text_auto=".2s",
        title="Amount by Branch"
    )

    fig_branch.update_layout(
        height=450,
        xaxis_title="Branch",
        yaxis_title="Amount"
    )

    fig_branch.update_yaxes(
        tickprefix="Rs. ",
        separatethousands=True
    )

    st.plotly_chart(
        fig_branch,
        use_container_width=True
    )


# ============================================================
# BRANCH QUANTITY
# ============================================================

with col2:

    st.markdown(
        '<div class="section-title">'
        ' Branch-wise Quantity'
        '</div>',
        unsafe_allow_html=True
    )

    fig_branch_qty = px.bar(
        branch_summary,
        x="branch",
        y="quantity",
        text_auto=".2s",
        title="Quantity by Branch"
    )

    fig_branch_qty.update_layout(
        height=450,
        xaxis_title="Branch",
        yaxis_title="Quantity"
    )

    st.plotly_chart(
        fig_branch_qty,
        use_container_width=True
    )


# ============================================================
# TOP 10 BRANCHES
# ============================================================

st.markdown(
    '<div class="section-title">'
    ' Top 10 Branches'
    '</div>',
    unsafe_allow_html=True
)

top_branches = (
    branch_summary
    .head(10)
    .sort_values("amount")
)

fig_top_branch = px.bar(
    top_branches,
    x="amount",
    y="branch",
    orientation="h",
    text_auto=".2s",
    title="Top 10 Branches by Amount"
)

fig_top_branch.update_layout(
    height=450,
    xaxis_title="Amount",
    yaxis_title="Branch"
)

fig_top_branch.update_xaxes(
    tickprefix="Rs. ",
    separatethousands=True
)

st.plotly_chart(
    fig_top_branch,
    use_container_width=True
)


# ============================================================
# ITEM ANALYSIS
# ============================================================

item_summary = (
    filtered_df
    .groupby(
        "description",
        as_index=False
    )
    .agg(
        amount=("amount", "sum"),
        quantity=("quantity", "sum")
    )
    .sort_values(
        "amount",
        ascending=False
    )
)


col1, col2 = st.columns(2)


# ============================================================
# TOP ITEMS BY AMOUNT
# ============================================================

with col1:

    st.markdown(
        '<div class="section-title">'
        ' Top 10 Items by Amount'
        '</div>',
        unsafe_allow_html=True
    )

    top_items_amount = (
        item_summary
        .head(10)
        .sort_values("amount")
    )

    fig_items_amount = px.bar(
        top_items_amount,
        x="amount",
        y="description",
        orientation="h",
        text_auto=".2s",
        title="Top Items by Amount"
    )

    fig_items_amount.update_layout(
        height=500,
        xaxis_title="Amount",
        yaxis_title="Item"
    )

    fig_items_amount.update_xaxes(
        tickprefix="Rs. ",
        separatethousands=True
    )

    st.plotly_chart(
        fig_items_amount,
        use_container_width=True
    )


# ============================================================
# TOP ITEMS BY QUANTITY
# ============================================================

with col2:

    st.markdown(
        '<div class="section-title">'
        ' Top 10 Items by Quantity'
        '</div>',
        unsafe_allow_html=True
    )

    top_items_quantity = (
        item_summary
        .sort_values(
            "quantity",
            ascending=False
        )
        .head(10)
        .sort_values("quantity")
    )

    fig_items_qty = px.bar(
        top_items_quantity,
        x="quantity",
        y="description",
        orientation="h",
        text_auto=".2s",
        title="Top Items by Quantity"
    )

    fig_items_qty.update_layout(
        height=500,
        xaxis_title="Quantity",
        yaxis_title="Item"
    )

    st.plotly_chart(
        fig_items_qty,
        use_container_width=True
    )


# ============================================================
# BRANCH CONTRIBUTION PIE
# ============================================================

col1, col2 = st.columns(2)


with col1:

    st.markdown(
        '<div class="section-title">'
        ' Branch Contribution'
        '</div>',
        unsafe_allow_html=True
    )

    pie_branch = branch_summary.head(10)

    fig_pie = px.pie(
        pie_branch,
        names="branch",
        values="amount",
        hole=0.4,
        title="Top Branch Contribution"
    )

    fig_pie.update_layout(
        height=500
    )

    st.plotly_chart(
        fig_pie,
        use_container_width=True
    )


# ============================================================
# UOM DISTRIBUTION
# ============================================================

with col2:

    st.markdown(
        '<div class="section-title">'
        ' UOM Distribution'
        '</div>',
        unsafe_allow_html=True
    )

    uom_summary = (
        filtered_df
        .groupby(
            "uom",
            as_index=False
        )
        ["quantity"]
        .sum()
        .sort_values(
            "quantity",
            ascending=False
        )
    )

    fig_uom = px.pie(
        uom_summary,
        names="uom",
        values="quantity",
        hole=0.4,
        title="Quantity by UOM"
    )

    fig_uom.update_layout(
        height=500
    )

    st.plotly_chart(
        fig_uom,
        use_container_width=True
    )


# ============================================================
# QUANTITY VS AMOUNT
# ============================================================

st.markdown(
    '<div class="section-title">'
    ' Quantity vs Amount'
    '</div>',
    unsafe_allow_html=True
)

scatter_df = filtered_df.copy()

fig_scatter = px.scatter(
    scatter_df,
    x="quantity",
    y="amount",
    color="branch",
    hover_data=[
        "inv_date",
        "inv_no",
        "description",
        "rate"
    ],
    title="Quantity vs Amount by Branch"
)

fig_scatter.update_layout(
    height=500,
    xaxis_title="Quantity",
    yaxis_title="Amount"
)

fig_scatter.update_yaxes(
    tickprefix="Rs. ",
    separatethousands=True
)

st.plotly_chart(
    fig_scatter,
    use_container_width=True
)


# ============================================================
# RATE ANALYSIS
# ============================================================

rate_df = filtered_df.copy()

rate_df = rate_df[
    (rate_df["rate"] > 0)
    |
    (rate_df["to_rate"] > 0)
]

if not rate_df.empty:

    st.markdown(
        '<div class="section-title">'
        ' Rate Analysis'
        '</div>',
        unsafe_allow_html=True
    )

    rate_summary = (
        rate_df
        .groupby("branch", as_index=False)
        .agg(
            avg_rate=("rate", "mean"),
            avg_to_rate=("to_rate", "mean")
        )
    )

    fig_rate = go.Figure()

    fig_rate.add_trace(
        go.Bar(
            x=rate_summary["branch"],
            y=rate_summary["avg_rate"],
            name="Average Rate"
        )
    )

    fig_rate.add_trace(
        go.Bar(
            x=rate_summary["branch"],
            y=rate_summary["avg_to_rate"],
            name="Average T.O Rate"
        )
    )

    fig_rate.update_layout(
        title="Average Rate vs T.O Rate by Branch",
        barmode="group",
        height=500,
        xaxis_title="Branch",
        yaxis_title="Rate"
    )

    st.plotly_chart(
        fig_rate,
        use_container_width=True
    )


# ============================================================
# DAY OF WEEK ANALYSIS
# ============================================================

st.markdown(
    '<div class="section-title">'
    ' Day-of-Week Analysis'
    '</div>',
    unsafe_allow_html=True
)

weekday_order = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]

weekday_summary = (
    filtered_df
    .groupby(
        "day_name",
        as_index=False
    )
    ["amount"]
    .sum()
)

weekday_summary["day_name"] = pd.Categorical(
    weekday_summary["day_name"],
    categories=weekday_order,
    ordered=True
)

weekday_summary = (
    weekday_summary
    .sort_values("day_name")
)

fig_weekday = px.bar(
    weekday_summary,
    x="day_name",
    y="amount",
    text_auto=".2s",
    title="Amount by Day of Week"
)

fig_weekday.update_layout(
    height=400,
    xaxis_title="Day",
    yaxis_title="Amount"
)

fig_weekday.update_yaxes(
    tickprefix="Rs. ",
    separatethousands=True
)

st.plotly_chart(
    fig_weekday,
    use_container_width=True
)


# ============================================================
# DAY OF MONTH
# ============================================================

day_summary = (
    filtered_df
    .groupby(
        "day",
        as_index=False
    )
    ["amount"]
    .sum()
    .sort_values("day")
)

fig_day = px.line(
    day_summary,
    x="day",
    y="amount",
    markers=True,
    title="Amount by Day of Month"
)

fig_day.update_layout(
    height=400,
    xaxis_title="Day of Month",
    yaxis_title="Amount"
)

fig_day.update_yaxes(
    tickprefix="Rs. ",
    separatethousands=True
)

st.plotly_chart(
    fig_day,
    use_container_width=True
)


# ============================================================
# Branch x Month
# ============================================================

st.markdown(
    '<div class="section-title">'
    ' Branch x Month Analysis'
    '</div>',
    unsafe_allow_html=True
)

branch_month = (
    filtered_df
    .groupby(
        ["branch", "month_year"],
        as_index=False
    )
    ["amount"]
    .sum()
)

if not branch_month.empty:

    pivot = branch_month.pivot(
        index="branch",
        columns="month_year",
        values="amount"
    ).fillna(0)

    fig_heatmap = px.imshow(
        pivot,
        text_auto=".2s",
        aspect="auto",
        title="Branch x Month Amount Heatmap"
    )

    fig_heatmap.update_layout(
        height=max(
            450,
            len(pivot) * 30
        ),
        xaxis_title="Month",
        yaxis_title="Branch"
    )

    st.plotly_chart(
        fig_heatmap,
        use_container_width=True
    )


# ============================================================
# CUMULATIVE AMOUNT
# ============================================================

st.markdown(
    '<div class="section-title">'
    ' Cumulative Amount'
    '</div>',
    unsafe_allow_html=True
)

cumulative = (
    daily.copy()
)

cumulative["cumulative_amount"] = (
    cumulative["amount"].cumsum()
)

fig_cumulative = px.area(
    cumulative,
    x="inv_date",
    y="cumulative_amount",
    title="Cumulative Supply Amount"
)

fig_cumulative.update_layout(
    height=450,
    xaxis_title="Date",
    yaxis_title="Cumulative Amount"
)

fig_cumulative.update_yaxes(
    tickprefix="Rs. ",
    separatethousands=True
)

st.plotly_chart(
    fig_cumulative,
    use_container_width=True
)


# ============================================================
# INVOICE ANALYSIS
# ============================================================

st.markdown(
    '<div class="section-title">'
    ' Invoice Analysis'
    '</div>',
    unsafe_allow_html=True
)

invoice_summary = (
    filtered_df
    .groupby(
        "inv_no",
        as_index=False
    )
    .agg(
        amount=("amount", "sum"),
        quantity=("quantity", "sum"),
        branch=("branch", "first"),
        inv_date=("inv_date", "first")
    )
    .sort_values(
        "amount",
        ascending=False
    )
)


top_invoices = (
    invoice_summary
    .head(15)
    .sort_values("amount")
)

fig_invoice = px.bar(
    top_invoices,
    x="amount",
    y="inv_no",
    color="branch",
    orientation="h",
    text_auto=".2s",
    title="Top 15 Invoices by Amount"
)

fig_invoice.update_layout(
    height=550,
    xaxis_title="Amount",
    yaxis_title="Invoice"
)

fig_invoice.update_xaxes(
    tickprefix="Rs. ",
    separatethousands=True
)

st.plotly_chart(
    fig_invoice,
    use_container_width=True
)


# ============================================================
# BRANCH SUMMARY TABLE
# ============================================================

st.markdown(
    '<div class="section-title">'
    ' Branch Summary'
    '</div>',
    unsafe_allow_html=True
)

display_branch = branch_summary.copy()

display_branch["amount"] = display_branch[
    "amount"
].round(2)

display_branch["quantity"] = display_branch[
    "quantity"
].round(2)

display_branch.columns = [
    "Branch",
    "Amount",
    "Quantity",
    "Invoices"
]

st.dataframe(
    display_branch,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Amount": st.column_config.NumberColumn(
            "Amount",
            format="Rs. %.0f"
        ),
        "Quantity": st.column_config.NumberColumn(
            "Quantity",
            format="%.0f"
        ),
        "Invoices": st.column_config.NumberColumn(
            "Invoices",
            format="%d"
        )
    }
)


# ============================================================
# TOP ITEMS TABLE
# ============================================================

st.markdown(
    '<div class="section-title">'
    ' Item Summary'
    '</div>',
    unsafe_allow_html=True
)

display_items = item_summary.head(50).copy()

display_items.columns = [
    "Description",
    "Amount",
    "Quantity"
]

st.dataframe(
    display_items,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Amount": st.column_config.NumberColumn(
            "Amount",
            format="Rs. %.0f"
        ),
        "Quantity": st.column_config.NumberColumn(
            "Quantity",
            format="%.0f"
        )
    }
)


# ============================================================
# DETAILED DATA
# ============================================================

st.markdown(
    '<div class="section-title">'
    ' Detailed Filtered Data'
    '</div>',
    unsafe_allow_html=True
)

display_df = filtered_df[
    [
        "id",
        "branch",
        "inv_date",
        "inv_no",
        "description",
        "uom",
        "quantity",
        "rate",
        "to_rate",
        "amount"
    ]
].copy()

display_df.columns = [
    "ID",
    "Branch",
    "Date",
    "Invoice No",
    "Description",
    "UOM",
    "Quantity",
    "Rate",
    "T.O Rate",
    "Amount"
]

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    height=600,
    column_config={
        "Date": st.column_config.DateColumn(
            "Date",
            format="DD-MMM-YYYY"
        ),
        "Quantity": st.column_config.NumberColumn(
            "Quantity",
            format="%.2f"
        ),
        "Rate": st.column_config.NumberColumn(
            "Rate",
            format="%.2f"
        ),
        "T.O Rate": st.column_config.NumberColumn(
            "T.O Rate",
            format="%.2f"
        ),
        "Amount": st.column_config.NumberColumn(
            "Amount",
            format="Rs. %.0f"
        )
    }
)


# ============================================================
# DOWNLOAD DATA
# ============================================================

st.markdown(
    '<div class="section-title">'
    ' Export'
    '</div>',
    unsafe_allow_html=True
)


csv_data = display_df.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="Download Filtered Data CSV",
    data=csv_data,
    file_name="OD_PAKISTAN_Filtered_Data.csv",
    mime="text/csv",
    use_container_width=True
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div style="
        text-align:center;
        color:#6b7280;
        padding:15px;
    ">
        OD PAKISTAN | Supply Management Dashboard
        <br>
        Powered by Streamlit + PostgreSQL / Supabase
    </div>
    """,
    unsafe_allow_html=True
)
