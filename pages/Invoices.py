import streamlit as st
import pandas as pd
import psycopg2
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED

from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import JsCode

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="OD PAKISTAN - Invoice Report",
    page_icon="🧾",
    layout="wide"
)


# ============================================================
# CUSTOM CSS — ELEGANT 3D THEME (matches supply_sheet app)
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


        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {

            border-bottom-color:
                rgba(255,255,255,.35);

        }


        /* =====================================================
           TITLE / SUBTITLE
           ===================================================== */

        .main-title {

            font-size: 32px;
            font-weight: 800;
            color: var(--od-ink);
            margin-bottom: 3px;

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

            color: var(--od-muted);
            font-size: 15px;
            margin-bottom: 20px;
            font-weight: 600;

        }


        /* =====================================================
           METRIC / KPI CARDS (raised 3D style)
           ===================================================== */

        .metric-card,
        [data-testid="stMetric"] {

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
                16px 18px;

            text-align: center;

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


        .metric-card:hover,
        [data-testid="stMetric"]:hover {

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


        .metric-title {

            font-size: 11px;
            font-weight: 600;
            color: var(--od-muted);
            text-transform: uppercase;
            letter-spacing: .06em;

            text-shadow:
                0 1px 0
                rgba(255,255,255,.9);

        }


        .metric-value {

            font-size: 22px;
            font-weight: 700;
            color: var(--od-ink);

            text-shadow:
                0 1px 0
                rgba(255,255,255,.9),

                0 2px 3px
                rgba(16,48,82,.18);

        }


        /* =====================================================
           SIDEBAR INPUTS — DATE / RADIO / SELECT / MULTISELECT
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


        .stTextInput label,
        .stTextArea label,
        .stDateInput label,
        .stRadio label,
        .stSelectbox label,
        .stMultiSelect label {

            font-weight: 600;
            color: var(--od-ink);

        }


        [data-testid="stRadio"] {

            background:
                linear-gradient(
                    180deg,
                    #ffffff 0%,
                    #eaf6ff 100%
                );

            border:
                1px solid #a9c6e0;

            border-radius: 9px;

            padding:
                8px 10px;

            box-shadow:
                inset 0 1px 0
                rgba(255,255,255,.95),

                inset 0 -2px 0
                rgba(16,48,82,.12),

                0 2px 0
                #a9c6e0,

                0 5px 10px
                rgba(16,48,82,.14);

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
           DATAFRAME PANELS (preview / generated file list)
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


        div[data-testid="stDataFrame"] .ag-cell,
        div[data-testid="stDataFrame"] div[class*="cell"] {

            font-family:
                "Segoe UI",
                "Aptos",
                "Calibri",
                sans-serif !important;

            font-weight: 600;

        }


        /* =====================================================
           INFO / WARNING BANNERS
           ===================================================== */

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
                0.75rem;

            margin-bottom:
                0.75rem;

        }

        </style>
        """,
        unsafe_allow_html=True
    )


apply_elegant_theme()


# ============================================================
# STYLED TABLE RENDERER
# (same navy/cyan header + embossed cell look as supply_sheet app)
# ============================================================

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


def render_styled_table(dataframe, height=350, center_columns=None, left_columns=None, fit_columns=False):
    """
    Renders a read-only AgGrid table with the same 3D
    navy/cyan header + embossed-cell theme used across
    the OD Pakistan apps.

    fit_columns=True stretches/shrinks every column to fit inside the
    table width so all columns are visible without horizontal
    scrolling — useful for wide tables with many columns.
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

    grid_custom_css = _grid_custom_css

    if left_columns:

        left_style_js = JsCode(
            """
            function(params) {
                return { 'textAlign': 'left' };
            }
            """
        )

        # Copy the shared theme CSS so this left-align override only
        # applies to this table, not every AgGrid table in the app
        grid_custom_css = dict(_grid_custom_css)
        grid_custom_css[".header-left-align .ag-header-cell-label"] = {
            "justify-content": "flex-start !important",
        }

        for col in left_columns:

            if col in dataframe.columns:

                gb.configure_column(
                    col,
                    headerClass="header-left-align",
                    cellStyle=left_style_js
                )

    if fit_columns:

        # Stretch every column to fill the available width so all
        # columns stay visible together, with no horizontal scrolling
        gb.configure_grid_options(
            rowHeight=34,
            headerHeight=34,
            onFirstDataRendered=JsCode(
                """
                function(params) {
                    setTimeout(function() {
                        params.api.sizeColumnsToFit();
                    }, 200);
                }
                """
            ),
            onGridSizeChanged=JsCode(
                """
                function(params) {
                    params.api.sizeColumnsToFit();
                }
                """
            )
        )

    else:

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
        fit_columns_on_grid_load=fit_columns,
        allow_unsafe_jscode=True,
        custom_css=grid_custom_css,
        enable_enterprise_modules=False
    )


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    try:

        # ----------------------------------------------------
        # DATABASE_URL method
        # ----------------------------------------------------

        if "DATABASE_URL" in st.secrets:

            return psycopg2.connect(
                st.secrets["DATABASE_URL"]
            )

        # ----------------------------------------------------
        # Individual database settings
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
def load_invoice_data():

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
        ORDER BY
            inv_date,
            branch,
            inv_no,
            id
    """

    try:

        df = pd.read_sql_query(
            query,
            conn
        )

    except Exception as e:

        st.error(
            "Unable to load data from supply_sheet."
        )

        st.code(str(e))

        st.stop()

    finally:

        conn.close()

    if df.empty:
        return df

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    df["inv_date"] = pd.to_datetime(
        df["inv_date"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # NUMERIC
    # --------------------------------------------------------

    numeric_columns = [
        "quantity",
        "rate",
        "to_rate",
        "amount"
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        ).fillna(0)

    # --------------------------------------------------------
    # TEXT
    # --------------------------------------------------------

    text_columns = [
        "branch",
        "inv_no",
        "description",
        "uom"
    ]

    for column in text_columns:

        df[column] = (
            df[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    return df


# ============================================================
# LOAD DATABASE DATA
# ============================================================

df = load_invoice_data()


# ============================================================
# CHECK EMPTY DATABASE
# ============================================================

if df.empty:

    st.warning(
        "No records found in supply_sheet."
    )

    st.stop()


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🧾 INVOICE REPORT</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">'
    'Generate individual invoice PDF files by date range and branch.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("🧾 Report Settings")

    st.divider()

    # ========================================================
    # DATE RANGE
    # ========================================================

    st.subheader("📅 Date Range")

    min_date = df["inv_date"].min().date()
    max_date = df["inv_date"].max().date()

    date_range = st.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(date_range, tuple):

        if len(date_range) == 2:

            start_date = date_range[0]
            end_date = date_range[1]

        elif len(date_range) == 1:

            start_date = date_range[0]
            end_date = date_range[0]

        else:

            start_date = min_date
            end_date = max_date

    else:

        start_date = date_range
        end_date = date_range

    # ========================================================
    # BRANCH
    # ========================================================

    st.divider()

    st.subheader("🏢 Branch Selection")

    branch_mode = st.radio(
        "Select Branch",
        [
            "All Branches",
            "Individual Branch",
            "Multiple Branches"
        ],
        index=0
    )

    branch_list = sorted(
        [
            branch
            for branch in df["branch"].unique()
            if branch
        ]
    )

    selected_branches = branch_list

    # --------------------------------------------------------
    # INDIVIDUAL
    # --------------------------------------------------------

    if branch_mode == "Individual Branch":

        selected_branch = st.selectbox(
            "Select Branch",
            branch_list
        )

        selected_branches = [
            selected_branch
        ]

    # --------------------------------------------------------
    # MULTIPLE
    # --------------------------------------------------------

    elif branch_mode == "Multiple Branches":

        selected_branches = st.multiselect(
            "Select Branches",
            branch_list,
            default=branch_list
        )

    # ========================================================
    # REFRESH
    # ========================================================

    st.divider()

    if st.button(
        "🔄 Refresh Database",
        use_container_width=True
    ):

        st.cache_data.clear()

        st.session_state.pop(
            "invoice_files",
            None
        )

        st.rerun()


# ============================================================
# FILTER DATA BY DATE
# ============================================================

report_df = df.copy()

report_df = report_df[
    (
        report_df["inv_date"].dt.date
        >= start_date
    )
    &
    (
        report_df["inv_date"].dt.date
        <= end_date
    )
]


# ============================================================
# FILTER BY BRANCH
# ============================================================

if branch_mode != "All Branches":

    if selected_branches:

        report_df = report_df[
            report_df["branch"].isin(
                selected_branches
            )
        ]

    else:

        report_df = report_df.iloc[0:0]


# ============================================================
# SEARCH (ALL COLUMNS) — narrows report_df before the KPI
# cards, preview table, and PDF generation are built, so
# everything downstream reflects the searched subset
# ============================================================

search_term = st.text_input(
    "🔍 Search invoices (searches every column)",
    value="",
    placeholder="Type a branch, item, invoice #, amount, date…"
)

if search_term.strip():

    searchable_df = report_df.copy()
    searchable_df["inv_date"] = searchable_df["inv_date"].dt.strftime("%d-%b-%Y")

    search_mask = (
        searchable_df
        .astype(str)
        .apply(
            lambda col: col.str.contains(
                search_term.strip(),
                case=False,
                na=False,
                regex=False
            )
        )
        .any(axis=1)
    )

    report_df = report_df[search_mask]


# ============================================================
# INVOICE GROUPS
# ============================================================

invoice_groups = (
    report_df[
        [
            "branch",
            "inv_date",
            "inv_no"
        ]
    ]
    .drop_duplicates()
)


invoice_count = len(
    invoice_groups
)

branch_count = report_df[
    "branch"
].nunique()

record_count = len(
    report_df
)

grand_total = report_df[
    "amount"
].sum()


# ============================================================
# KPI CARDS — SAME RAISED 3D CARD STYLE AS SUPPLY SHEET APP
# ============================================================

card_style = """
    height:64px;
    padding:6px 10px;
    box-sizing:border-box;
    text-align:center;

    border:1px solid #8fabc4;
    border-radius:9px;

    background:linear-gradient(
        180deg,
        #e4eff8 0%,
        #ffffff 26%
    );

    box-shadow:
        inset 0 3px 6px rgba(16,32,51,.26),
        inset 0 -2px 0 rgba(255,255,255,.95),
        0 1px 0 rgba(255,255,255,.9);

    font-family:"Segoe UI","Aptos","Calibri",sans-serif;
"""


def kpi_label(text):

    return f"""
        <div style="
            font-size:11px;
            font-weight:600;
            color:#30465a;
            line-height:15px;
            text-transform:uppercase;
            letter-spacing:.05em;
        ">
            {text}
        </div>
    """


def kpi_value(text):

    return f"""
        <div style="
            font-size:20px;
            font-weight:700;
            color:#102033;
            line-height:26px;
            text-shadow:0 1px 0 rgba(255,255,255,.6);
        ">
            {text}
        </div>
    """


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.html(f"""
    <div style="{card_style}">
        {kpi_label("Total Invoices")}
        {kpi_value(f"{invoice_count:,}")}
    </div>
    """)


with col2:

    st.html(f"""
    <div style="{card_style}">
        {kpi_label("Branches")}
        {kpi_value(f"{branch_count:,}")}
    </div>
    """)


with col3:

    st.html(f"""
    <div style="{card_style}">
        {kpi_label("Records")}
        {kpi_value(f"{record_count:,}")}
    </div>
    """)


with col4:

    st.html(f"""
    <div style="{card_style}">
        {kpi_label("Grand Total")}
        {kpi_value(f"{grand_total:,.0f}")}
    </div>
    """)


# ============================================================
# FILTER INFORMATION
# ============================================================

st.write("")

if branch_mode == "All Branches":

    branch_text = "All Branches"

else:

    branch_text = ", ".join(
        selected_branches
    )


st.info(
    f"📅 **Date Range:** "
    f"{start_date.strftime('%d-%b-%Y')} "
    f"to "
    f"{end_date.strftime('%d-%b-%Y')} "
    f"   |   "
    f"🏢 **Branch:** {branch_text} "
    f"   |   "
    f"🧾 **Invoices:** {invoice_count:,}"
)


# ============================================================
# NO DATA
# ============================================================

if report_df.empty:

    st.warning(
        "No invoices found for the selected "
        "date range and branch."
    )

    st.stop()


# ============================================================
# INVOICE PREVIEW
# ============================================================

st.subheader("📋 Invoices to Generate")


preview = report_df.copy()


preview["Bar Code"] = ""   # not present in the data — shown blank, same as the PDF

preview["T.O #"] = preview["to_rate"].map(
    lambda x: f"{x:,.2f}" if pd.notna(x) and x != 0 else ""
)

preview["Date"] = (
    preview["inv_date"]
    .dt.strftime("%d-%b-%Y")
)

preview["Quantity"] = (
    preview["quantity"]
    .map(lambda x: f"{x:,.2f}")
)

preview["Rate"] = (
    preview["rate"]
    .map(lambda x: f"{x:,.2f}")
)

preview["T.O Rate"] = (
    preview["to_rate"]
    .map(lambda x: f"{x:,.2f}")
)

preview["Amount"] = (
    preview["amount"]
    .map(lambda x: f"{x:,.0f}")
)

preview = preview.rename(
    columns={
        "branch": "Branch",
        "inv_no": "Invoice No",
        "description": "Description",
    }
)

preview = preview[
    [
        "Bar Code",
        "T.O #",
        "Branch",
        "Date",
        "Invoice No",
        "Description",
        "Quantity",
        "Rate",
        "T.O Rate",
        "Amount",
    ]
]


render_styled_table(
    preview,
    height=400,
    center_columns=["Bar Code", "T.O #", "Branch", "Date", "Invoice No", "Quantity", "Rate", "T.O Rate", "Amount"],
    left_columns=["Description"],
    fit_columns=True
)


# ============================================================
# NUMBER FORMAT
# ============================================================

def money(value):

    try:

        return f"{float(value):,.2f}"

    except Exception:

        return "0.00"


def qty(value):

    try:

        return f"{float(value):,.2f}"

    except Exception:

        return "0.00"


# ============================================================
# SAFE FILE NAME
# ============================================================

def safe_filename(value):

    value = str(value)

    invalid_characters = [
        "/",
        "\\",
        ":",
        "*",
        "?",
        '"',
        "<",
        ">",
        "|"
    ]

    for character in invalid_characters:

        value = value.replace(
            character,
            "-"
        )

    return value.strip()


# ============================================================
# CREATE INDIVIDUAL PDF
# ============================================================

def create_invoice_pdf(
    invoice_df,
    branch,
    invoice_date,
    invoice_no
):

    from io import BytesIO
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle
    )
    from reportlab.pdfgen import canvas as reportlab_canvas

    buffer = BytesIO()

    # ========================================================
    # BRAND PALETTE — matches the app's elegant 3D theme
    # ========================================================

    INK = colors.HexColor("#102033")
    MUTED = colors.HexColor("#5d6f86")
    LINE = colors.HexColor("#8fabc4")
    LINE_SOFT = colors.HexColor("#c4d7eb")
    ACCENT = colors.HexColor("#00a6c8")
    ACCENT_DARK = colors.HexColor("#0b7795")
    HEADER_BG = colors.HexColor("#0e5772")
    TOTAL_BG = colors.HexColor("#eaf6ff")
    ROW_ALT_BG = colors.HexColor("#f5f9fc")
    SHADOW = colors.HexColor("#c9dcec")

    # ========================================================
    # PAGE
    # ========================================================

    PAGE_WIDTH, PAGE_HEIGHT = A4

    LEFT_MARGIN = 8 * mm
    RIGHT_MARGIN = 8 * mm
    HEADER_HEIGHT = 57 * mm          # room reserved for the drawn letterhead
    TOP_MARGIN = HEADER_HEIGHT
    BOTTOM_MARGIN = 8 * mm

    AVAILABLE_WIDTH = (
        PAGE_WIDTH
        - LEFT_MARGIN
        - RIGHT_MARGIN
    )

    # ========================================================
    # STYLES
    # ========================================================

    styles = getSampleStyleSheet()

    header_style = ParagraphStyle(
        "HeaderStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.4,
        leading=11.3,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    header_left_style = ParagraphStyle(
        "HeaderLeftStyle",
        parent=header_style,
        alignment=TA_LEFT
    )

    normal_style = ParagraphStyle(
        "NormalStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.4,
        leading=11.3,
        alignment=TA_LEFT,
        textColor=INK
    )

    center_style = ParagraphStyle(
        "CenterStyle",
        parent=normal_style,
        alignment=TA_CENTER
    )

    right_style = ParagraphStyle(
        "RightStyle",
        parent=normal_style,
        alignment=TA_RIGHT
    )

    total_label_style = ParagraphStyle(
        "TotalLabelStyle",
        parent=normal_style,
        fontSize=10.6,
        alignment=TA_CENTER,
        textColor=ACCENT_DARK
    )

    total_value_style = ParagraphStyle(
        "TotalValueStyle",
        parent=normal_style,
        fontSize=10.6,
        alignment=TA_CENTER,
        textColor=INK
    )

    # ========================================================
    # PREPARE DATA
    # ========================================================

    df = invoice_df.copy()
    df = df.dropna(how="all")

    def find_column(possible_names):
        for col in df.columns:
            clean_col = str(col).strip().lower()
            for name in possible_names:
                if name in clean_col:
                    return col
        return None

    description_col = find_column(["description", "particular", "item", "item name"])
    uom_col = find_column(["uom", "unit"])
    quantity_col = find_column(["quantity", "qty"])
    rate_col = find_column(["rate"])
    amount_col = find_column(["amount", "total"])
    to_number_col = find_column(["to_rate", "t.o #", "to #", "t.o rate", "to rate", "torate"])

    # ========================================================
    # T.O # — pulled straight from the data's T.O # column
    # (first non-empty / non-zero value found for this invoice)
    # ========================================================

    to_number_header = ""

    if to_number_col:

        for raw_value in df[to_number_col].tolist():

            if pd.isna(raw_value):
                continue

            text_value = str(raw_value).strip()

            if text_value in ("", "0", "0.0", "0.00"):
                continue

            try:
                number = float(text_value.replace(",", ""))
                text_value = f"{number:,.2f}" if number % 1 else f"{number:,.0f}"
            except Exception:
                pass

            to_number_header = text_value
            break

    date_text_header = (
        pd.Timestamp(invoice_date).strftime("%d-%B-%Y")
        if pd.notna(invoice_date)
        else str(invoice_date)
    )

    # ========================================================
    # LETTERHEAD — drawn directly on the canvas of every page
    # (repeats automatically if an invoice spills onto page 2, 3…)
    # ========================================================

    def draw_shadowed_text(pdf_canvas, x, y, text, font, size, ink_color, align="left"):
        """Light offset copy behind the main glyph gives a subtle
        embossed / 3D look to the big letterhead titles."""

        pdf_canvas.setFont(font, size)
        pdf_canvas.setFillColor(SHADOW)

        draw_fn = {
            "left": pdf_canvas.drawString,
            "center": pdf_canvas.drawCentredString,
            "right": pdf_canvas.drawRightString,
        }[align]

        draw_fn(x + 0.35 * mm, y - 0.35 * mm, text)

        pdf_canvas.setFillColor(ink_color)
        draw_fn(x, y, text)

    def draw_letterhead(pdf_canvas, page_label, page_number):

        pdf_canvas.saveState()

        top_y = PAGE_HEIGHT - 8.75 * mm

        # -- Brand row (embossed OD wordmark) --------------------------
        draw_shadowed_text(
            pdf_canvas, PAGE_WIDTH / 2, top_y,
            "OD", "Helvetica-Bold", 22.5, INK, align="center"
        )

        pdf_canvas.setFont("Helvetica", 9.4)
        pdf_canvas.setFillColor(MUTED)
        pdf_canvas.drawRightString(
            PAGE_WIDTH - RIGHT_MARGIN, top_y + 1.9 * mm, page_label
        )

        pdf_canvas.setFont("Helvetica-Bold", 11.25)
        pdf_canvas.setFillColor(ACCENT_DARK)
        pdf_canvas.drawCentredString(
            PAGE_WIDTH / 2, top_y - 6.875 * mm, "OverDose"
        )

        draw_shadowed_text(
            pdf_canvas, PAGE_WIDTH / 2, top_y - 15.625 * mm,
            "INVOICE", "Helvetica-Bold", 17.5, INK, align="center"
        )

        # -- Accent divider (gradient-style band) -----------------------
        band_y = top_y - 20 * mm
        band_steps = 40
        for i in range(band_steps):
            t = i / (band_steps - 1)
            r = 0x00 + t * (0x8f - 0x00)
            g = 0xa6 + t * (0xab - 0xa6)
            b = 0xc8 + t * (0xc4 - 0xc8)
            pdf_canvas.setStrokeColor(colors.Color(r / 255, g / 255, b / 255))
            x0 = LEFT_MARGIN + (AVAILABLE_WIDTH * i / band_steps)
            x1 = LEFT_MARGIN + (AVAILABLE_WIDTH * (i + 1) / band_steps)
            pdf_canvas.setLineWidth(1.1)
            pdf_canvas.line(x0, band_y, x1, band_y)

        # -- Customer Name / Date / Invoice # / T.O # -------------------
        # Only shown on page 1 — page 2, 3, and onward just keep the
        # brand heading above (OD / OverDose / INVOICE) plus the item
        # table's own repeating column headings.
        if page_number == 1:

            left_x = LEFT_MARGIN
            right_label_x = PAGE_WIDTH - RIGHT_MARGIN - 48 * mm

            row1_y = band_y - 6.875 * mm
            row2_y = row1_y - 6.25 * mm
            row3_y = row2_y - 6.25 * mm    # T.O # label
            row4_y = row3_y - 6.25 * mm    # T.O # value — its own row, up to 30 chars

            pdf_canvas.setFont("Helvetica-Bold", 9.4)
            pdf_canvas.setFillColor(MUTED)
            pdf_canvas.drawString(left_x, row1_y, "CUSTOMER NAME")

            pdf_canvas.setFont("Helvetica-Bold", 13.1)
            pdf_canvas.setFillColor(INK)
            pdf_canvas.drawString(left_x, row2_y, str(branch))

            pdf_canvas.setFont("Helvetica-Bold", 9.4)
            pdf_canvas.setFillColor(MUTED)
            pdf_canvas.drawString(right_label_x, row1_y, "DATE")
            pdf_canvas.setFont("Helvetica-Bold", 10.6)
            pdf_canvas.setFillColor(INK)
            pdf_canvas.drawString(right_label_x + 20 * mm, row1_y, date_text_header)

            pdf_canvas.setFont("Helvetica-Bold", 9.4)
            pdf_canvas.setFillColor(MUTED)
            pdf_canvas.drawString(right_label_x, row2_y, "INVOICE #")
            pdf_canvas.setFont("Helvetica-Bold", 10.6)
            pdf_canvas.setFillColor(INK)
            pdf_canvas.drawString(right_label_x + 20 * mm, row2_y, str(invoice_no))

            # T.O # — label on its own row, value directly below on the next
            # row (kept on two rows since the value can run up to 30 characters).
            # The value is right-aligned to the page's right margin so it always
            # has room to grow leftward regardless of how long it is.
            pdf_canvas.setFont("Helvetica-Bold", 9.4)
            pdf_canvas.setFillColor(MUTED)
            pdf_canvas.drawString(right_label_x, row3_y, "T.O #")

            pdf_canvas.setFont("Helvetica-Bold", 8.75)
            pdf_canvas.setFillColor(INK)
            pdf_canvas.drawRightString(
                PAGE_WIDTH - RIGHT_MARGIN, row4_y, to_number_header
            )

        pdf_canvas.restoreState()

    # ========================================================
    # NUMBERED CANVAS — draws the letterhead + "Page X of Y" on
    # every physical page once the final page count is known
    # ========================================================

    class NumberedCanvas(reportlab_canvas.Canvas):

        def __init__(self, *args, **kwargs):
            reportlab_canvas.Canvas.__init__(self, *args, **kwargs)
            self._saved_page_states = []

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total_pages = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                page_label = f"Page {self._pageNumber} of {total_pages}"
                draw_letterhead(self, page_label, self._pageNumber)
                reportlab_canvas.Canvas.showPage(self)
            reportlab_canvas.Canvas.save(self)

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN
    )

    story = []

    # ========================================================
    # COLUMN LAYOUT
    #
    # S.No / Bar Code / Item Name / UoM / Qty / Rate / Amount
    #
    # - "Bar Code" isn't in the data, so it's left blank per row.
    # - Branch, Date, Invoice # and T.O # now live in the
    #   letterhead, so they're no longer table columns.
    # ========================================================

    columns = [("S.No", None), ("Bar Code", None)]

    if description_col:
        columns.append(("Item Name", description_col))
    if uom_col:
        columns.append(("UoM", uom_col))
    if quantity_col:
        columns.append(("Qty", quantity_col))
    if rate_col:
        columns.append(("Rate", rate_col))
    if amount_col:
        columns.append(("Amount", amount_col))

    numeric_display_names = ["Qty", "Rate", "Amount"]
    center_display_names = ["S.No", "Bar Code", "UoM"]

    item_name_index = next(
        (i for i, (name, _) in enumerate(columns) if name == "Item Name"),
        None
    )
    qty_index = next(
        (i for i, (name, _) in enumerate(columns) if name == "Qty"),
        None
    )
    amount_index = next(
        (i for i, (name, _) in enumerate(columns) if name == "Amount"),
        None
    )

    def format_cell(display_name, original_col, row_number, row):

        if display_name == "S.No":
            return str(row_number)

        if display_name == "Bar Code":
            return ""

        value = row.get(original_col, "")

        if pd.isna(value):
            value = ""

        value = str(value)

        if display_name in numeric_display_names:
            try:
                number = float(str(value).replace(",", "").strip())
                value = f"{number:,.0f}" if display_name == "Amount" else f"{number:,.2f}"
            except Exception:
                pass

        return (
            value
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    # ========================================================
    # HEADER ROW
    # ========================================================

    table_data = [[
        Paragraph(str(display_name), header_left_style if display_name == "Item Name" else header_style)
        for display_name, _ in columns
    ]]

    # ========================================================
    # DATA ROWS — S.No numbered sequentially 1, 2, 3, 4… for
    # each invoice
    # ========================================================

    for row_number, (_, row) in enumerate(df.iterrows(), start=1):

        pdf_row = []

        for display_name, original_col in columns:

            value = format_cell(display_name, original_col, row_number, row)

            if display_name in numeric_display_names:
                pdf_row.append(Paragraph(value, center_style))
            elif display_name in center_display_names:
                pdf_row.append(Paragraph(value, center_style))
            else:
                pdf_row.append(Paragraph(value, normal_style))

        table_data.append(pdf_row)

    item_row_count = len(table_data) - 1  # excludes header row

    # ========================================================
    # TOTAL ROW — appended into the same grid so it lines up
    # perfectly under Item Name / Qty / Amount, one row below
    # the last item
    # ========================================================

    total_quantity = (
        pd.to_numeric(df[quantity_col], errors="coerce").fillna(0).sum()
        if quantity_col else None
    )
    total_amount = (
        pd.to_numeric(df[amount_col], errors="coerce").fillna(0).sum()
        if amount_col else None
    )

    total_row = ["" for _ in columns]

    total_label_index = item_name_index if item_name_index is not None else 0
    total_row[total_label_index] = Paragraph("TOTAL", total_label_style)

    if qty_index is not None and total_quantity is not None:
        total_row[qty_index] = Paragraph(f"{total_quantity:,.2f}", total_value_style)

    if amount_index is not None and total_amount is not None:
        total_row[amount_index] = Paragraph(f"{total_amount:,.0f}", total_value_style)

    total_row = [
        cell if isinstance(cell, Paragraph) else Paragraph("", normal_style)
        for cell in total_row
    ]

    # A blank spacer row separates the items from TOTAL by one row
    spacer_row = [Paragraph("", normal_style) for _ in columns]

    spacer_row_idx = len(table_data)
    table_data.append(spacer_row)

    table_data.append(total_row)

    total_row_idx = len(table_data) - 1

    # ========================================================
    # AUTO-FIT COLUMN WIDTHS — every column sized from its own
    # content (header + longest cell), then scaled proportionally
    # so the table exactly spans the page width
    # ========================================================

    MIN_WIDTH = 13 * mm
    MAX_WIDTH = 115 * mm
    CHAR_WIDTH = 2.625 * mm

    column_widths = []

    for display_name, original_col in columns:

        longest_text = len(display_name)

        if display_name == "S.No":
            longest_text = max(longest_text, len(str(item_row_count)))

        elif display_name == "Bar Code":
            longest_text = max(longest_text, len("Bar Code"))

        elif display_name == "Amount":
            for value in df[original_col].tolist() if original_col else []:
                if pd.isna(value):
                    continue
                try:
                    number = float(str(value).replace(",", "").strip())
                    text = f"{number:,.0f}"
                except Exception:
                    text = str(value)
                longest_text = max(longest_text, min(len(text), 60))
            if total_amount is not None:
                longest_text = max(longest_text, len(f"{total_amount:,.0f}"))

        elif display_name == "Qty" and total_quantity is not None:
            longest_text = max(longest_text, len(f"{total_quantity:,.2f}"))
            for value in df[original_col].tolist():
                if pd.isna(value):
                    continue
                text = str(value)
                try:
                    number = float(str(text).replace(",", "").strip())
                    text = f"{number:,.2f}"
                except Exception:
                    pass
                longest_text = max(longest_text, min(len(text), 60))

        elif original_col is not None:
            for value in df[original_col].tolist():
                if pd.isna(value):
                    continue
                text = str(value)
                if display_name in numeric_display_names:
                    try:
                        number = float(str(text).replace(",", "").strip())
                        text = f"{number:,.2f}"
                    except Exception:
                        pass
                longest_text = max(longest_text, min(len(text), 60))

        width = max(longest_text * CHAR_WIDTH, MIN_WIDTH)
        width = min(width, MAX_WIDTH)

        # Manual width boosts for specific columns (applied on top of
        # the autofit base width, before the page-width scaling below)
        WIDTH_BOOST = {
            "UoM": 1.50,
            "Qty": 1.50,
            "Rate": 1.10,
            "Amount": 1.50,
        }
        width *= WIDTH_BOOST.get(display_name, 1.0)

        column_widths.append(width)

    # Scale to fit the page width — S.No and Bar Code are kept at their
    # own content-fit width (never squeezed below what their text needs);
    # the remaining columns absorb the scaling to make up the difference
    protected_names = ("S.No", "Bar Code")

    protected_total = sum(
        w for (display_name, _), w in zip(columns, column_widths)
        if display_name in protected_names
    )

    scalable_total = sum(
        w for (display_name, _), w in zip(columns, column_widths)
        if display_name not in protected_names
    )

    remaining_available = AVAILABLE_WIDTH - protected_total

    if scalable_total > 0 and remaining_available > 0:
        scale = remaining_available / scalable_total
        column_widths = [
            w if display_name in protected_names else w * scale
            for (display_name, _), w in zip(columns, column_widths)
        ]

    # ========================================================
    # TABLE
    # ========================================================

    invoice_table = Table(
        table_data,
        colWidths=column_widths,
        repeatRows=1,
        hAlign="LEFT"
    )

    table_style_commands = [
        # -- Header row -------------------------------------------------
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("LINEBELOW", (0, 0), (-1, 0), 1.4, ACCENT),

        # -- Grid (items only — spacer row stays borderless) -------------
        ("GRID", (0, 0), (-1, spacer_row_idx - 1), 0.4, LINE_SOFT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        # -- Padding --------------------------------------------------------
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),

        # -- Alternating item rows -------------------------------------
        ("ROWBACKGROUNDS", (0, 1), (-1, spacer_row_idx - 1), [colors.white, ROW_ALT_BG]),

        # -- Blank spacer row: one clear row of empty space between the
        # -- last item and TOTAL, no grid lines
        ("BACKGROUND", (0, spacer_row_idx), (-1, spacer_row_idx), colors.white),
        ("TOPPADDING", (0, spacer_row_idx), (-1, spacer_row_idx), 1.9),
        ("BOTTOMPADDING", (0, spacer_row_idx), (-1, spacer_row_idx), 1.9),

        # -- Total row: "TOTAL" centred in the Item Name column only,
        # -- no spanning; light background, clearly separated -----------
        ("BACKGROUND", (0, total_row_idx), (-1, total_row_idx), TOTAL_BG),
        ("LINEABOVE", (0, total_row_idx), (-1, total_row_idx), 1.2, ACCENT_DARK),
        ("BOX", (0, total_row_idx), (-1, total_row_idx), 0.6, LINE),
        ("TOPPADDING", (0, total_row_idx), (-1, total_row_idx), 5.6),
        ("BOTTOMPADDING", (0, total_row_idx), (-1, total_row_idx), 5.6),
    ]

    invoice_table.setStyle(TableStyle(table_style_commands))

    story.append(invoice_table)

    # ========================================================
    # BUILD PDF (NumberedCanvas draws the letterhead + Page X of Y)
    # ========================================================

    doc.build(story, canvasmaker=NumberedCanvas)

    buffer.seek(0)

    return buffer.getvalue()


# ============================================================
# GENERATE ALL INDIVIDUAL INVOICE FILES
# ============================================================

def create_invoice_files(dataframe):

    invoice_files = []

    grouped = (
        dataframe
        .sort_values(
            [
                "inv_date",
                "branch",
                "inv_no",
                "id"
            ]
        )
        .groupby(
            [
                "branch",
                "inv_date",
                "inv_no"
            ],
            sort=False
        )
    )


    for (
        (
            branch,
            invoice_date,
            invoice_no
        ),
        invoice_data
    ) in grouped:

        # ----------------------------------------------------
        # Branch
        # ----------------------------------------------------

        safe_branch = safe_filename(
            branch
        )

        # ----------------------------------------------------
        # Invoice
        # ----------------------------------------------------

        safe_invoice = safe_filename(
            invoice_no
        )

        # ----------------------------------------------------
        # Date
        # ----------------------------------------------------

        if pd.notna(invoice_date):

            date_text = pd.Timestamp(
                invoice_date
            ).strftime(
                "%d-%b-%Y"
            )

        else:

            date_text = "Unknown-Date"


        # ----------------------------------------------------
        # PDF filename — branch is included so files stay
        # uniquely named once everything sits in one flat
        # folder inside the ZIP (no more per-branch subfolders)
        # ----------------------------------------------------

        if safe_invoice:

            filename = (
                f"{safe_branch}_"
                f"{date_text}_"
                f"{safe_invoice}.pdf"
            )

        else:

            filename = (
                f"{safe_branch}_"
                f"{date_text}_Invoice.pdf"
            )


        # ----------------------------------------------------
        # Generate PDF
        # ----------------------------------------------------

        pdf_data = create_invoice_pdf(
            invoice_data,
            branch,
            invoice_date,
            invoice_no
        )


        invoice_files.append(
            {
                "branch": safe_branch,
                "date": date_text,
                "invoice_no": safe_invoice,
                "filename": filename,
                "data": pdf_data
            }
        )


    return invoice_files


# ============================================================
# GENERATE BUTTON
# ============================================================

st.divider()


if st.button(
    "📄 GENERATE INVOICE PDF FILES",
    type="primary",
    use_container_width=True
):

    with st.spinner(
        f"Generating "
        f"{invoice_count:,} individual invoice PDF(s)..."
    ):

        try:

            invoice_files = create_invoice_files(
                report_df
            )

            st.session_state[
                "invoice_files"
            ] = invoice_files

            st.success(
                f"Successfully generated "
                f"{len(invoice_files):,} invoice PDF(s)."
            )

        except Exception as e:

            st.error(
                "PDF generation failed."
            )

            st.exception(e)


# ============================================================
# DOWNLOAD SECTION
# ============================================================

if "invoice_files" in st.session_state:

    invoice_files = st.session_state[
        "invoice_files"
    ]

    if invoice_files:

        st.divider()

        st.subheader(
            "📥 Download Invoice Files"
        )


        # ====================================================
        # ONE COMBINED ZIP — always available, whatever the
        # branch selection (All / Individual / Multiple). Every
        # PDF sits inside one single folder in the ZIP — no
        # per-branch subfolders. Filenames already carry the
        # branch name so files stay uniquely identifiable.
        # ====================================================

        zip_buffer = BytesIO()

        zip_root_folder = (
            "OD_PAKISTAN_Invoices_"
            f"{start_date.strftime('%Y%m%d')}_"
            f"{end_date.strftime('%Y%m%d')}"
        )

        with ZipFile(
            zip_buffer,
            "w",
            ZIP_DEFLATED
        ) as zip_file:

            for invoice in invoice_files:

                # ------------------------------------------------
                # IMPORTANT:
                #
                # ZIP structure — one flat folder, everything inside:
                #
                # OD_PAKISTAN_Invoices_.../
                #     Branch_Date_InvoiceNo.pdf
                #     Branch_Date_InvoiceNo.pdf
                #     ...
                # ------------------------------------------------

                zip_path = (
                    f"{zip_root_folder}/"
                    f"{invoice['filename']}"
                )

                zip_file.writestr(
                    zip_path,
                    invoice["data"]
                )

        zip_buffer.seek(0)

        zip_filename = f"{zip_root_folder}.zip"

        # ====================================================
        # SINGLE INVOICE — offer a direct PDF download alongside
        # the ZIP option, for convenience
        # ====================================================

        if len(invoice_files) == 1:

            invoice = invoice_files[0]

            col_single, col_zip = st.columns(2)

            with col_single:

                st.download_button(
                    label="⬇️ Download Invoice PDF",
                    data=invoice["data"],
                    file_name=invoice["filename"],
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )

            with col_zip:

                st.download_button(
                    label="⬇️ Download as ZIP (Branch Folder)",
                    data=zip_buffer.getvalue(),
                    file_name=zip_filename,
                    mime="application/zip",
                    use_container_width=True
                )

        # ====================================================
        # MULTIPLE INVOICES — one ZIP, invoices grouped by
        # branch folder (covers All Branches, Individual Branch
        # with several invoices, and Multiple Branches alike)
        # ====================================================

        else:

            st.download_button(
                label=(
                    f"⬇️ Download "
                    f"{len(invoice_files):,} "
                    f"Invoices as ZIP"
                ),
                data=zip_buffer.getvalue(),
                file_name=zip_filename,
                mime="application/zip",
                type="primary",
                use_container_width=True
            )

            st.info(
                "ZIP structure: "
                "**one folder containing every invoice PDF** — "
                "no branch subfolders. "
                "Each filename includes the branch, date, and invoice number."
            )


# ============================================================
# GENERATED FILE LIST
# ============================================================

if "invoice_files" in st.session_state:

    invoice_files = st.session_state[
        "invoice_files"
    ]

    if invoice_files:

        st.divider()

        st.subheader(
            "📄 Generated Invoice Files"
        )


        generated_data = []


        for invoice in invoice_files:

            generated_data.append(
                {
                    "Branch": invoice[
                        "branch"
                    ],

                    "Date": invoice[
                        "date"
                    ],

                    "Invoice No": invoice[
                        "invoice_no"
                    ],

                    "PDF File": invoice[
                        "filename"
                    ]
                }
            )


        generated_df = pd.DataFrame(
            generated_data
        )


        render_styled_table(
            generated_df,
            height=400,
            center_columns=["Branch", "Date", "Invoice No"],
            left_columns=["PDF File"],
            fit_columns=True
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
        padding:12px;
    ">
        OD PAKISTAN | Invoice Report
        <br>
        Date Range → Branch → Individual Invoice PDFs
    </div>
    """,
    unsafe_allow_html=True
)
