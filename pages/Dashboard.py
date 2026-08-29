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
    page_title="OD PAKISTAN - DASHBOARD",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS — ELEGANT 3D THEME (matches supply_sheet / invoice apps)
# ============================================================

def apply_elegant_theme():

    st.markdown(
        """
        <style>

        :root {

            --od-ink: #102033;
            --od-muted: #5d6f86;
            --od-line: #c4d7eb;
            --od-soft: #f3f8ff;
            --od-panel: #ffffff;
            --od-accent: #00a6c8;
            --od-accent-dark: #075e7a;
            --od-gold: #d69b2d;

        }


        .stApp {

            background:
                radial-gradient(
                    circle at 12% 8%,
                    rgba(0, 166, 200, .16),
                    transparent 28%
                ),
                radial-gradient(
                    circle at 86% 6%,
                    rgba(69, 94, 181, .14),
                    transparent 26%
                ),
                linear-gradient(
                    180deg,
                    #f6fbff 0%,
                    #eaf3fb 48%,
                    #f7f9fc 100%
                );

            color: var(--od-ink);

            font-family:
                "Segoe UI",
                "Inter",
                "Aptos",
                "Calibri",
                sans-serif;

        }


        .block-container {

            padding-top: 0.75rem;
            padding-bottom: 0.75rem;

            max-width: 100%;

        }


        h1, h2, h3 {

            font-family:
                "Segoe UI Semibold",
                "Segoe UI",
                "Inter",
                sans-serif;

            letter-spacing: 0;

            color: var(--od-ink);

            text-shadow:
                0 1px 0
                rgba(255,255,255,.85),
                0 -1px 0
                rgba(16,32,51,.15);

        }


        h2, h3 {

            padding-bottom: 6px;

            border-bottom:
                1px solid var(--od-line);

        }


        /* =====================================================
           MAIN TITLE / SUBTITLE
           ===================================================== */

        .main-title {

            font-size: 32px;
            font-weight: 800;
            color: var(--od-ink);
            margin-bottom: 0px;

            font-family:
                "Segoe UI Semibold",
                "Segoe UI",
                "Inter",
                sans-serif;

            text-shadow:
                0 1px 0
                rgba(255,255,255,.85),
                0 -1px 0
                rgba(16,32,51,.15);

        }

        .sub-title {

            font-size: 15px;
            color: var(--od-muted);
            font-weight: 600;
            margin-bottom: 20px;

        }


        /* =====================================================
           SECTION TITLES (raised, accent-underlined)
           ===================================================== */

        .section-title {

            font-size: 20px;
            font-weight: 700;
            color: var(--od-ink);
            margin-top: 22px;
            margin-bottom: 12px;
            padding-bottom: 8px;

            font-family:
                "Segoe UI Semibold",
                "Segoe UI",
                "Inter",
                sans-serif;

            text-shadow:
                0 1px 0
                rgba(255,255,255,.85),
                0 -1px 0
                rgba(16,32,51,.15);

            border-bottom:
                2px solid var(--od-accent);

            box-shadow:
                0 1px 0
                rgba(255,255,255,.9);

        }


        /* =====================================================
           KPI CARDS (raised 3D style)
           ===================================================== */

        .kpi-card {

            background:
                linear-gradient(
                    180deg,
                    #ffffff 0%,
                    #eaf6ff 40%,
                    #cde3f5 100%
                );

            border:
                1px solid var(--od-line);

            border-radius: 10px;

            padding:
                16px 16px;

            min-height: 125px;

            box-shadow:
                0 2px 0
                rgba(255,255,255,1)
                inset,

                0 -3px 4px
                rgba(16,48,82,.16)
                inset,

                0 1px 0
                #ffffff,

                0 4px 0
                #93b8d6,

                0 18px 32px
                rgba(16,48,82,.26);

            transition:
                transform .12s ease,
                box-shadow .12s ease;

        }


        .kpi-card:hover {

            transform:
                translateY(-3px);

            box-shadow:
                0 2px 0
                rgba(255,255,255,1)
                inset,

                0 -3px 4px
                rgba(16,48,82,.16)
                inset,

                0 1px 0
                #ffffff,

                0 6px 0
                #93b8d6,

                0 22px 36px
                rgba(16,48,82,.30);

        }


        .kpi-title {

            font-size: 12px;
            color: var(--od-muted);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: .05em;

            text-shadow:
                0 1px 0
                rgba(255,255,255,.9);

        }


        .kpi-value {

            font-size: 24px;
            font-weight: 700;
            color: var(--od-ink);
            margin-top: 8px;

            text-shadow:
                0 1px 0
                rgba(255,255,255,.9),

                0 2px 3px
                rgba(16,48,82,.18);

        }


        .kpi-small {

            font-size: 11px;
            color: var(--od-muted);
            margin-top: 5px;
            font-weight: 600;

        }


        /* =====================================================
           SIDEBAR — LIGHT ELEGANT THEME
           ===================================================== */

        section[data-testid="stSidebar"] {

            background:
                linear-gradient(
                    180deg,
                    #eaf3fb 0%,
                    #dcebf7 100%
                );

            border-right:
                1px solid var(--od-line);

        }


        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] label {

            color: var(--od-ink) !important;

        }


        /* =====================================================
           INPUTS — TEXT / DATE / SELECT / MULTISELECT
           ===================================================== */

        .stTextInput input,
        .stTextArea textarea,
        [data-baseweb="select"] > div,
        [data-testid="stDateInput"] input {

            border:
                1px solid #8fabc4 !important;

            border-radius: 9px !important;

            background:
                linear-gradient(
                    180deg,
                    #e4eff8 0%,
                    #ffffff 26%
                ) !important;

            box-shadow:
                inset 0 3px 6px
                rgba(16,32,51,.26),

                inset 0 -2px 0
                rgba(255,255,255,.95),

                0 1px 0
                rgba(255,255,255,.9) !important;

            font-family:
                "Segoe UI",
                "Aptos",
                "Calibri",
                sans-serif;

            font-weight: 700;

            color: var(--od-ink) !important;

        }


        .stTextInput input:focus,
        .stTextArea textarea:focus,
        [data-baseweb="select"] > div:focus-within {

            border-color:
                var(--od-accent) !important;

            box-shadow:
                inset 0 3px 7px
                rgba(16,32,51,.32),

                inset 0 -2px 0
                rgba(255,255,255,.95),

                0 0 0 3px
                rgba(0,166,200,.25) !important;

        }


        /* =====================================================
           BUTTONS
           ===================================================== */

        .stButton > button,
        .stDownloadButton > button {

            border-radius: 7px;

            border:
                1px solid #7fa5c3;

            background:
                linear-gradient(
                    180deg,
                    #ffffff 0%,
                    #d9f1ff 52%,
                    #bfdff2 100%
                );

            color: var(--od-ink);

            font-weight: 700;

            box-shadow:
                inset 0 1px 0
                rgba(255,255,255,.98),

                inset 0 -2px 0
                rgba(16,48,82,.16),

                0 2px 0
                #7fa5c3,

                0 8px 16px
                rgba(16,48,82,.18);

        }


        .stButton > button[kind="primary"],
        .stDownloadButton > button[kind="primary"] {

            border-color:
                var(--od-accent-dark);

            background:
                linear-gradient(
                    180deg,
                    #35d5ec 0%,
                    #0d8bac 48%,
                    #075e7a 100%
                );

            color: #ffffff;

        }


        /* =====================================================
           CHART PANELS (embossed frame around every Plotly chart)
           ===================================================== */

        div[data-testid="stVerticalBlockBorderWrapper"] {

            background:
                linear-gradient(
                    180deg,
                    #ffffff 0%,
                    #eef6fc 100%
                );

            border:
                1px solid #92b8d8 !important;

            border-radius: 12px !important;

            box-shadow:
                0 2px 0
                rgba(255,255,255,1)
                inset,

                0 -3px 5px
                rgba(16,48,82,.14)
                inset,

                0 1px 0
                #ffffff,

                0 4px 0
                #93b8d6,

                0 14px 26px
                rgba(16,48,82,.22);

            padding: 6px;

            margin-bottom: 10px;

        }


        /* =====================================================
           DATAFRAME PANELS
           ===================================================== */

        div[data-testid="stDataFrame"] {

            border:
                1px solid #92b8d8;

            border-radius: 8px;

            box-shadow:
                0 2px 0
                rgba(255,255,255,1)
                inset,

                0 -3px 5px
                rgba(16,48,82,.14)
                inset,

                0 4px 0
                #93b8d6,

                0 12px 22px
                rgba(16,48,82,.20);

            overflow: hidden;

        }


        [data-testid="stAlert"] {

            border-radius: 9px;

            border:
                1px solid #a9c6e0;

            box-shadow:
                inset 0 1px 0
                rgba(255,255,255,.9),

                0 4px 10px
                rgba(16,48,82,.12);

        }


        hr {

            border-color:
                #d7e0ea;

            margin-top:
                10px;

            margin-bottom:
                10px;

        }

        </style>
        """,
        unsafe_allow_html=True
    )


apply_elegant_theme()


# ============================================================
# STYLED TABLE RENDERER
# (same navy/cyan header + embossed cell look as other OD apps)
# ============================================================

from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import JsCode


_grid_custom_css = {

    ".ag-root-wrapper": {

        "border":
            "1px solid #92b8d8 !important",

        "border-radius":
            "8px !important",

        "box-shadow":
            "0 18px 34px rgba(16,48,82,.18), inset 0 1px 0 #ffffff !important",

        "overflow":
            "hidden !important"

    },


    ".ag-header": {

        "background":
            "linear-gradient(180deg, #0b7795 0%, #102b4e 100%) !important",

        "border-bottom":
            "2px solid #38d5ec !important"

    },


    ".ag-header-cell": {

        "border-right":
            "1px solid rgba(255,255,255,.22) !important",

        "box-shadow":
            "inset 2px 2px 0 rgba(255,255,255,.38), inset -2px -2px 3px rgba(0,0,0,.38) !important"

    },


    ".ag-header-cell-label": {

        "font-family":
            "Segoe UI, Aptos, Calibri, sans-serif !important",

        "font-weight":
            "600 !important",

        "justify-content":
            "center !important"

    },


    ".ag-header-cell-text": {

        "font-family":
            "Segoe UI, Aptos, Calibri, sans-serif !important",

        "font-weight":
            "600 !important",

        "color":
            "#ffffff !important",

        "font-size":
            "12px !important",

        "text-transform":
            "uppercase !important",

        "text-shadow":
            "0 1px 1px rgba(0,0,0,.45) !important"

    },


    ".ag-cell": {

        "border-color":
            "#d7e7f5 !important",

        "border-left":
            "1px solid rgba(255,255,255,.95) !important",

        "border-top":
            "1px solid rgba(255,255,255,.92) !important",

        "font-family":
            "Segoe UI, Aptos, Calibri, sans-serif !important",

        "font-weight":
            "600 !important",

        "color":
            "#1f2937 !important",

        "font-size":
            "13px !important",

        "line-height":
            "34px !important",

        "padding-left":
            "9px !important",

        "padding-right":
            "9px !important",

        "box-shadow":
            "inset 0 1px 0 rgba(255,255,255,.9), inset 0 -3px 4px rgba(16,48,82,.10) !important",

        "text-shadow":
            "0 1px 0 rgba(255,255,255,.7) !important"

    },


    ".ag-cell-focus": {

        "box-shadow":
            "inset 0 0 0 2px #38d5ec !important"

    },


    ".ag-row-hover": {

        "background-color":
            "#dcf7ff !important"

    },


    ".ag-row-odd": {

        "background-color":
            "#f4fbff !important"

    }

}


def render_styled_table(dataframe, height=350, center_columns=None):
    """
    Renders a read-only AgGrid table with the same 3D
    navy/cyan header + embossed-cell theme used across
    the OD Pakistan apps.
    """

    if dataframe.empty:

        st.dataframe(
            dataframe,
            use_container_width=True,
            hide_index=True
        )

        return

    gb = GridOptionsBuilder.from_dataframe(dataframe)

    gb.configure_default_column(
        resizable=True,
        sortable=True,
        filter=True,
        floatingFilter=False,
        editable=False,
        minWidth=60
    )

    if center_columns:

        center_style_js = JsCode(
            """
            function(params) {
                return { 'textAlign': 'center' };
            }
            """
        )

        for col in center_columns:

            if col in dataframe.columns:

                gb.configure_column(
                    col,
                    cellStyle=center_style_js
                )

    gb.configure_grid_options(
        rowHeight=34,
        headerHeight=34,
        onFirstDataRendered=JsCode(
            """
            function(params) {
                setTimeout(function() {
                    params.api.autoSizeAllColumns(false);
                }, 200);
            }
            """
        )
    )

    grid_options = gb.build()

    AgGrid(
        dataframe,
        gridOptions=grid_options,
        height=height,
        fit_columns_on_grid_load=False,
        allow_unsafe_jscode=True,
        custom_css=_grid_custom_css,
        enable_enterprise_modules=False
    )


# ============================================================
# CHART THEME
# (embossed 3D bar effect + bold navy/cyan fonts on every axis)
# ============================================================

OD_INK = "#102033"
OD_MUTED = "#5d6f86"
OD_ACCENT = "#00a6c8"
OD_ACCENT_DARK = "#075e7a"
OD_GOLD = "#d69b2d"
OD_LINE = "#c4d7eb"

OD_COLORWAY = [
    "#0d8bac",
    "#d69b2d",
    "#5f8ee8",
    "#38d5ec",
    "#8a5fd6",
    "#e8735f",
    "#4fae7a",
    "#c95fb0",
    "#c4a13a",
    "#3a7fc9"
]


def style_chart(fig, title=None):
    """
    Applies the shared OD Pakistan "3D" chart theme:
    bold embossed axis-title fonts, navy/cyan colorway,
    beveled bar/marker outlines, and a transparent panel
    background so the chart sits inside the embossed
    card wrapper.
    """

    # --------------------------------------------------------
    # BEVELED / "3D" LOOK ON BARS
    # --------------------------------------------------------

    fig.update_traces(
        marker=dict(
            line=dict(
                width=1.2,
                color="rgba(16,48,82,0.45)"
            )
        ),
        selector=dict(type="bar")
    )

    fig.for_each_trace(
        lambda trace: trace.update(
            marker=dict(
                line=dict(
                    width=1.5,
                    color="#ffffff"
                )
            )
        )
        if trace.type == "pie"
        else None
    )

    # --------------------------------------------------------
    # COLORWAY
    # --------------------------------------------------------

    fig.update_layout(
        colorway=OD_COLORWAY
    )

    # --------------------------------------------------------
    # FONTS / BACKGROUND / TITLE
    # --------------------------------------------------------

    fig.update_layout(

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.55)",

        font=dict(
            family="Segoe UI, Aptos, Calibri, sans-serif",
            color=OD_INK,
            size=13
        ),

        title=dict(
            text=title if title else fig.layout.title.text,
            font=dict(
                family="Segoe UI Semibold, Segoe UI, sans-serif",
                color=OD_ACCENT_DARK,
                size=17
            ),
            x=0.02,
            xanchor="left"
        ),

        legend=dict(
            font=dict(
                family="Segoe UI, Aptos, Calibri, sans-serif",
                color=OD_INK,
                size=12
            ),
            bgcolor="rgba(255,255,255,0.6)",
            bordercolor=OD_LINE,
            borderwidth=1
        ),

        hoverlabel=dict(
            bgcolor=OD_ACCENT_DARK,
            font=dict(
                family="Segoe UI, Aptos, Calibri, sans-serif",
                color="#ffffff",
                size=12
            ),
            bordercolor="#38d5ec"
        ),

        margin=dict(l=40, r=30, t=55, b=40)

    )

    # --------------------------------------------------------
    # AXIS TITLES — BOLD "RAISED" NAVY, 3D-STYLE GRID
    # --------------------------------------------------------

    axis_title_font = dict(
        family="Segoe UI Semibold, Segoe UI, sans-serif",
        size=14,
        color=OD_ACCENT_DARK
    )

    axis_tick_font = dict(
        family="Segoe UI, Aptos, Calibri, sans-serif",
        size=11,
        color=OD_MUTED
    )

    fig.update_xaxes(
        title_font=axis_title_font,
        tickfont=axis_tick_font,
        showline=True,
        linewidth=2,
        linecolor="#8fabc4",
        gridcolor="rgba(143,171,196,0.25)",
        zerolinecolor="#8fabc4"
    )

    fig.update_yaxes(
        title_font=axis_title_font,
        tickfont=axis_tick_font,
        showline=True,
        linewidth=2,
        linecolor="#8fabc4",
        gridcolor="rgba(143,171,196,0.25)",
        zerolinecolor="#8fabc4"
    )

    return fig


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


# ============================================================
# LOAD DATA
# ============================================================

df = load_data()


# ============================================================
# EMPTY DATABASE CHECK
# ============================================================

if df.empty:

    st.title("📊 OD PAKISTAN - DASHBOARD")

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
            color:#102033;
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
            color:#5d6f86;
            margin-top:0px;
            font-weight:600;
        ">
        Supply Dashboard
        </p>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    st.subheader("🔎 Filters")

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
        "Description Search"
    )

    # --------------------------------------------------------
    # Invoice Search
    # --------------------------------------------------------

    invoice_search = st.text_input(
        "Invoice No Search"
    )

    st.divider()

    if st.button(
        "🔄 Refresh Database",
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
            na=False
        )
    ]


# Invoice search

if invoice_search:

    filtered_df = filtered_df[
        filtered_df["inv_no"]
        .str.contains(
            invoice_search,
            case=False,
            na=False
        )
    ]


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">📊 OD PAKISTAN - DASHBOARD</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">'
    'Interactive Supply, Invoice & Branch Analysis'
    '</div>',
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
            <div class="kpi-title">💰 Total Amount</div>
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
            <div class="kpi-title">📦 Quantity</div>
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
            <div class="kpi-title">🧾 Records</div>
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
            <div class="kpi-title">🧾 Invoices</div>
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
            <div class="kpi-title">🏢 Branches</div>
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
            <div class="kpi-title">📊 Avg Invoice</div>
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
    '📈 Daily Amount Trend'
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

style_chart(fig_daily)

with st.container(border=True):

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
        '📅 Monthly Amount'
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

    style_chart(fig_month)

    with st.container(border=True):

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
        '📦 Monthly Quantity'
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

    style_chart(fig_month_qty)

    with st.container(border=True):

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
        '🏢 Branch-wise Amount'
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

    style_chart(fig_branch)

    with st.container(border=True):

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
        '📦 Branch-wise Quantity'
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

    style_chart(fig_branch_qty)

    with st.container(border=True):

        st.plotly_chart(
            fig_branch_qty,
            use_container_width=True
        )


# ============================================================
# TOP 10 BRANCHES
# ============================================================

st.markdown(
    '<div class="section-title">'
    '🏆 Top 10 Branches'
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

style_chart(fig_top_branch)

with st.container(border=True):

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
        '📦 Top 10 Items by Amount'
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

    style_chart(fig_items_amount)

    with st.container(border=True):

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
        '📦 Top 10 Items by Quantity'
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

    style_chart(fig_items_qty)

    with st.container(border=True):

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
        '🥧 Branch Contribution'
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

    style_chart(fig_pie)

    with st.container(border=True):

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
        '📏 UOM Distribution'
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

    style_chart(fig_uom)

    with st.container(border=True):

        st.plotly_chart(
            fig_uom,
            use_container_width=True
        )


# ============================================================
# QUANTITY VS AMOUNT
# ============================================================

st.markdown(
    '<div class="section-title">'
    '🔵 Quantity vs Amount'
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

style_chart(fig_scatter)

with st.container(border=True):

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
        '💰 Rate Analysis'
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

    style_chart(fig_rate)

    with st.container(border=True):

        st.plotly_chart(
            fig_rate,
            use_container_width=True
        )


# ============================================================
# DAY OF WEEK ANALYSIS
# ============================================================

st.markdown(
    '<div class="section-title">'
    '📅 Day-of-Week Analysis'
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

style_chart(fig_weekday)

with st.container(border=True):

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

style_chart(fig_day)

with st.container(border=True):

    st.plotly_chart(
        fig_day,
        use_container_width=True
    )


# ============================================================
# BRANCH × MONTH
# ============================================================

st.markdown(
    '<div class="section-title">'
    '🏢📅 Branch × Month Analysis'
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
        title="Branch × Month Amount Heatmap"
    )

    fig_heatmap.update_layout(
        height=max(
            450,
            len(pivot) * 30
        ),
        xaxis_title="Month",
        yaxis_title="Branch"
    )

    style_chart(fig_heatmap)

    with st.container(border=True):

        st.plotly_chart(
            fig_heatmap,
            use_container_width=True
        )


# ============================================================
# CUMULATIVE AMOUNT
# ============================================================

st.markdown(
    '<div class="section-title">'
    '📈 Cumulative Amount'
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

style_chart(fig_cumulative)

with st.container(border=True):

    st.plotly_chart(
        fig_cumulative,
        use_container_width=True
    )


# ============================================================
# INVOICE ANALYSIS
# ============================================================

st.markdown(
    '<div class="section-title">'
    '🧾 Invoice Analysis'
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

style_chart(fig_invoice)

with st.container(border=True):

    st.plotly_chart(
        fig_invoice,
        use_container_width=True
    )


# ============================================================
# BRANCH SUMMARY TABLE
# ============================================================

st.markdown(
    '<div class="section-title">'
    '📋 Branch Summary'
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

render_styled_table(
    display_branch,
    height=350,
    center_columns=["Branch", "Invoices"]
)


# ============================================================
# TOP ITEMS TABLE
# ============================================================

st.markdown(
    '<div class="section-title">'
    '📦 Item Summary'
    '</div>',
    unsafe_allow_html=True
)

display_items = item_summary.head(50).copy()

display_items.columns = [
    "Description",
    "Amount",
    "Quantity"
]

render_styled_table(
    display_items,
    height=400
)


# ============================================================
# DETAILED DATA
# ============================================================

st.markdown(
    '<div class="section-title">'
    '📋 Detailed Filtered Data'
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

render_styled_table(
    display_df,
    height=600,
    center_columns=["ID", "Branch", "Date", "Invoice No", "UOM"]
)


# ============================================================
# DOWNLOAD DATA
# ============================================================

st.markdown(
    '<div class="section-title">'
    '📥 Export'
    '</div>',
    unsafe_allow_html=True
)


csv_data = display_df.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="📥 Download Filtered Data CSV",
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