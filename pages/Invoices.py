import streamlit as st
import pandas as pd
import psycopg2
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED

from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import JsCode

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
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
# CUSTOM CSS
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

            color: var(--od-ink);

            text-shadow:
                0 1px 0 rgba(255,255,255,.85),
                0 -1px 0 rgba(16,32,51,.15);
        }

        h2, h3 {
            padding-bottom: 6px;
            border-bottom: 1px solid var(--od-line);
        }

        .main-title {
            font-size: 32px;
            font-weight: 800;
            color: var(--od-ink);
            margin-bottom: 3px;
        }

        .sub-title {
            color: var(--od-muted);
            font-size: 15px;
            margin-bottom: 20px;
            font-weight: 600;
        }

        .metric-card,
        [data-testid="stMetric"] {
            background:
                linear-gradient(
                    180deg,
                    #ffffff 0%,
                    #eaf6ff 40%,
                    #cde3f5 100%
                );

            border: 1px solid var(--od-line);
            border-radius: 10px;
            padding: 16px 18px;

            text-align: center;

            box-shadow:
                0 2px 0 rgba(255,255,255,1) inset,
                0 -3px 4px rgba(16,48,82,.16) inset,
                0 1px 0 #ffffff,
                0 4px 0 #93b8d6,
                0 18px 32px rgba(16,48,82,.26);
        }

        .stTextInput input,
        .stTextArea textarea,
        [data-baseweb="select"] > div,
        [data-testid="stDateInput"] input {
            border: 1px solid #8fabc4 !important;
            border-radius: 9px !important;

            background:
                linear-gradient(
                    180deg,
                    #e4eff8 0%,
                    #ffffff 26%
                ) !important;

            box-shadow:
                inset 0 3px 6px rgba(16,32,51,.26),
                inset 0 -2px 0 rgba(255,255,255,.95),
                0 1px 0 rgba(255,255,255,.9) !important;

            font-weight: 700;
            color: var(--od-ink) !important;
        }

        .stButton > button,
        .stDownloadButton > button {
            border-radius: 7px;

            border: 1px solid #7fa5c3;

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
                inset 0 1px 0 rgba(255,255,255,.98),
                inset 0 -2px 0 rgba(16,48,82,.16),
                0 2px 0 #7fa5c3,
                0 8px 16px rgba(16,48,82,.18);
        }

        .stButton > button[kind="primary"],
        .stDownloadButton > button[kind="primary"] {
            border-color: var(--od-accent-dark);

            background:
                linear-gradient(
                    180deg,
                    #35d5ec 0%,
                    #0d8bac 48%,
                    #075e7a 100%
                );

            color: #ffffff;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid #92b8d8;
            border-radius: 8px;

            box-shadow:
                0 2px 0 rgba(255,255,255,1) inset,
                0 -3px 5px rgba(16,48,82,.14) inset,
                0 4px 0 #93b8d6,
                0 12px 22px rgba(16,48,82,.20);

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

        [data-testid="stAlert"] {
            border-radius: 9px;
            border: 1px solid #a9c6e0;

            box-shadow:
                inset 0 1px 0 rgba(255,255,255,.9),
                0 4px 10px rgba(16,48,82,.12);
        }

        hr {
            border-color: #d7e0ea;
            margin-top: 0.75rem;
            margin-bottom: 0.75rem;
        }

        </style>
        """,
        unsafe_allow_html=True
    )


apply_elegant_theme()


# ============================================================
# AGGRID CSS
# ============================================================

_grid_custom_css = {

    ".ag-root-wrapper": {
        "border": "1px solid #92b8d8 !important",
        "border-radius": "8px !important",
        "box-shadow":
            "0 18px 34px rgba(16,48,82,.18), "
            "inset 0 1px 0 #ffffff !important",
        "overflow": "hidden !important"
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
            "inset 2px 2px 0 rgba(255,255,255,.38), "
            "inset -2px -2px 3px rgba(0,0,0,.38) !important"
    },

    ".ag-header-cell-label": {
        "font-family":
            "Segoe UI, Aptos, Calibri, sans-serif !important",
        "font-weight": "600 !important",
        "justify-content": "center !important"
    },

    ".ag-header-cell-text": {
        "font-family":
            "Segoe UI, Aptos, Calibri, sans-serif !important",
        "font-weight": "600 !important",
        "color": "#ffffff !important",
        "font-size": "12px !important",
        "text-transform": "uppercase !important",
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
        "font-weight": "600 !important",
        "color": "#1f2937 !important",
        "font-size": "13px !important",
        "line-height": "34px !important",
        "padding-left": "9px !important",
        "padding-right": "9px !important",
        "box-shadow":
            "inset 0 1px 0 rgba(255,255,255,.9), "
            "inset 0 -3px 4px rgba(16,48,82,.10) !important",
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
    },

    ".ag-floating-filter": {
        "background":
            "#eaf6ff !important",
        "border-bottom":
            "1px solid #92b8d8 !important"
    },

    ".ag-floating-filter-input": {
        "font-family":
            "Segoe UI, Aptos, Calibri, sans-serif !important",
        "font-size": "12px !important"
    },

    ".ag-floating-filter-input input": {
        "border":
            "1px solid #8fabc4 !important",
        "border-radius":
            "5px !important",
        "background":
            "#ffffff !important",
        "color":
            "#102033 !important",
        "padding":
            "2px 6px !important"
    },

    ".ag-header-icon, .ag-header-cell-menu-button": {
        "color":
            "#ffffff !important",
        "opacity":
            "0.9 !important"
    },

    ".ag-side-bar": {
        "border-left":
            "1px solid #cbd6e2 !important"
    }
}


# ============================================================
# STYLED TABLE
# ============================================================

def render_styled_table(
    dataframe,
    height=350,
    center_columns=None,
    left_columns=None,
    fit_columns=False
):

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
        filter="agTextColumnFilter",
        floatingFilter=True,
        editable=False,
        minWidth=60,
        filterParams={
            "buttons": ["reset", "apply"],
            "defaultJoinOperator": "AND"
        }
    )

    numeric_filter_columns = (
        "Quantity",
        "Rate",
        "T.O Rate",
        "Amount",
        "Records",
        "quantity",
        "rate",
        "to_rate",
        "amount",
        "records"
    )

    for col in dataframe.columns:

        if col in numeric_filter_columns:

            gb.configure_column(
                col,
                filter="agNumberColumnFilter",
                floatingFilter=True
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

        grid_custom_css = dict(_grid_custom_css)

        grid_custom_css[
            ".header-left-align .ag-header-cell-label"
        ] = {
            "justify-content":
                "flex-start !important",
        }

        for col in left_columns:

            if col in dataframe.columns:

                gb.configure_column(
                    col,
                    headerClass="header-left-align",
                    cellStyle=left_style_js
                )

    gb.configure_side_bar(
        filters_panel=True,
        columns_panel=True
    )

    if fit_columns:

        gb.configure_grid_options(
            rowHeight=34,
            headerHeight=34,
            floatingFiltersHeight=32,

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
            floatingFiltersHeight=32,

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

        if "DATABASE_URL" in st.secrets:

            return psycopg2.connect(
                st.secrets["DATABASE_URL"]
            )

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
            branch,
            inv_date,
            description,
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

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        ).fillna(0)

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
# DATA
# ============================================================

df = load_invoice_data()


if df.empty:

    st.warning(
        "No records found in supply_sheet."
    )

    st.stop()


# ============================================================
# PAGE HEADER
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

    if branch_mode == "Individual Branch":

        selected_branch = st.selectbox(
            "Select Branch",
            branch_list
        )

        selected_branches = [
            selected_branch
        ]

    elif branch_mode == "Multiple Branches":

        selected_branches = st.multiselect(
            "Select Branches",
            branch_list,
            default=branch_list
        )

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
# FILTER BY DATE
# ============================================================

report_df = df.copy()

report_df = report_df[
    (
        report_df["inv_date"].dt.date >= start_date
    )
    &
    (
        report_df["inv_date"].dt.date <= end_date
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
# SEARCH
# ============================================================

search_term = st.text_input(
    "🔍 Quick Search — searches all columns",
    value="",
    placeholder="Type a branch, item, invoice #, amount, date…"
)

if search_term.strip():

    searchable_df = report_df.copy()

    searchable_df["inv_date"] = (
        searchable_df["inv_date"]
        .dt.strftime("%d-%b-%Y")
    )

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
# KPI
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

invoice_count = len(invoice_groups)

branch_count = report_df["branch"].nunique()

record_count = len(report_df)

grand_total = report_df["amount"].sum()


# ============================================================
# KPI CARDS
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

    st.html(
        f"""
        <div style="{card_style}">
            {kpi_label("Total Invoices")}
            {kpi_value(f"{invoice_count:,}")}
        </div>
        """
    )


with col2:

    st.html(
        f"""
        <div style="{card_style}">
            {kpi_label("Branches")}
            {kpi_value(f"{branch_count:,}")}
        </div>
        """
    )


with col3:

    st.html(
        f"""
        <div style="{card_style}">
            {kpi_label("Records")}
            {kpi_value(f"{record_count:,}")}
        </div>
        """
    )


with col4:

    st.html(
        f"""
        <div style="{card_style}">
            {kpi_label("Grand Total")}
            {kpi_value(f"{grand_total:,.0f}")}
        </div>
        """
    )


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


if report_df.empty:

    st.warning(
        "No invoices found for the selected "
        "date range and branch."
    )

    st.stop()


# ============================================================
# PREVIEW
# ============================================================

st.subheader("📋 Invoices to Generate")

preview = report_df.copy()

preview["Bar Code"] = ""

preview["T.O #"] = preview["to_rate"].map(
    lambda x:
        f"{x:,.2f}"
        if pd.notna(x) and x != 0
        else ""
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
    center_columns=[
        "Bar Code",
        "T.O #",
        "Branch",
        "Date",
        "Invoice No",
        "Quantity",
        "Rate",
        "T.O Rate",
        "Amount"
    ],
    left_columns=["Description"],
    fit_columns=True
)


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

    buffer = BytesIO()

    # ========================================================
    # COLORS
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

    PAGE_WIDTH, PAGE_HEIGHT = A4

    LEFT_MARGIN = 8 * mm
    RIGHT_MARGIN = 8 * mm

    # ========================================================
    # IMPORTANT PAGE MARGINS
    #
    # PAGE 1:
    # Large top margin because the complete letterhead is shown.
    #
    # PAGE 2+:
    # Very small top margin.
    # Page number is at the very top.
    # Column headings therefore start immediately underneath.
    # ========================================================

    FIRST_PAGE_TOP_MARGIN = 57 * mm

    OTHER_PAGE_TOP_MARGIN = 13 * mm

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
    # DATA
    # ========================================================

    df = invoice_df.copy()

    df = df.dropna(how="all")

    def find_column(possible_names):

        for col in df.columns:

            clean_col = (
                str(col)
                .strip()
                .lower()
            )

            for name in possible_names:

                if name in clean_col:

                    return col

        return None

    description_col = find_column(
        [
            "description",
            "particular",
            "item",
            "item name"
        ]
    )

    uom_col = find_column(
        [
            "uom",
            "unit"
        ]
    )

    quantity_col = find_column(
        [
            "quantity",
            "qty"
        ]
    )

    rate_col = find_column(
        [
            "rate"
        ]
    )

    amount_col = find_column(
        [
            "amount",
            "total"
        ]
    )

    to_number_col = find_column(
        [
            "to_rate",
            "t.o #",
            "to #",
            "t.o rate",
            "to rate",
            "torate"
        ]
    )

    # ========================================================
    # T.O #
    # ========================================================

    to_number_header = ""

    if to_number_col:

        for raw_value in df[
            to_number_col
        ].tolist():

            if pd.isna(raw_value):
                continue

            text_value = str(
                raw_value
            ).strip()

            if text_value in (
                "",
                "0",
                "0.0",
                "0.00"
            ):
                continue

            try:

                number = float(
                    text_value.replace(
                        ",",
                        ""
                    )
                )

                if number % 1:

                    text_value = (
                        f"{number:,.2f}"
                    )

                else:

                    text_value = (
                        f"{number:,.0f}"
                    )

            except Exception:
                pass

            to_number_header = text_value

            break

    # ========================================================
    # DATE
    # ========================================================

    date_text_header = (
        pd.Timestamp(
            invoice_date
        ).strftime("%d-%B-%Y")
        if pd.notna(invoice_date)
        else str(invoice_date)
    )

    # ========================================================
    # LETTERHEAD
    #
    # Page 1:
    # Full letterhead.
    #
    # Page 2+:
    # Only Page X of Y.
    # ========================================================

    def draw_shadowed_text(
        pdf_canvas,
        x,
        y,
        text,
        font,
        size,
        ink_color,
        align="left"
    ):

        pdf_canvas.setFont(
            font,
            size
        )

        pdf_canvas.setFillColor(
            SHADOW
        )

        draw_fn = {
            "left":
                pdf_canvas.drawString,

            "center":
                pdf_canvas.drawCentredString,

            "right":
                pdf_canvas.drawRightString,
        }[align]

        draw_fn(
            x + 0.35 * mm,
            y - 0.35 * mm,
            text
        )

        pdf_canvas.setFillColor(
            ink_color
        )

        draw_fn(
            x,
            y,
            text
        )

    def draw_letterhead(
        pdf_canvas,
        page_label,
        page_number
    ):

        pdf_canvas.saveState()

        # ====================================================
        # PAGE NUMBER
        #
        # Always at top.
        # ====================================================

        page_number_y = (
            PAGE_HEIGHT
            - 7 * mm
        )

        pdf_canvas.setFont(
            "Helvetica-Bold",
            9
        )

        pdf_canvas.setFillColor(
            MUTED
        )

        pdf_canvas.drawRightString(
            PAGE_WIDTH - RIGHT_MARGIN,
            page_number_y,
            page_label
        )

        # ====================================================
        # PAGE 1 ONLY
        # ====================================================

        if page_number == 1:

            top_y = (
                PAGE_HEIGHT
                - 8.75 * mm
            )

            # -----------------------------------------------
            # OD
            # -----------------------------------------------

            draw_shadowed_text(
                pdf_canvas,
                PAGE_WIDTH / 2,
                top_y,
                "OD",
                "Helvetica-Bold",
                22.5,
                INK,
                align="center"
            )

            # -----------------------------------------------
            # OverDose
            # -----------------------------------------------

            pdf_canvas.setFont(
                "Helvetica-Bold",
                11.25
            )

            pdf_canvas.setFillColor(
                ACCENT_DARK
            )

            pdf_canvas.drawCentredString(
                PAGE_WIDTH / 2,
                top_y - 6.875 * mm,
                "OverDose"
            )

            # -----------------------------------------------
            # INVOICE
            # -----------------------------------------------

            draw_shadowed_text(
                pdf_canvas,
                PAGE_WIDTH / 2,
                top_y - 15.625 * mm,
                "INVOICE",
                "Helvetica-Bold",
                17.5,
                INK,
                align="center"
            )

            # -----------------------------------------------
            # ACCENT LINE
            # -----------------------------------------------

            band_y = (
                top_y
                - 20 * mm
            )

            band_steps = 40

            for i in range(
                band_steps
            ):

                t = (
                    i /
                    (band_steps - 1)
                )

                r = (
                    0x00
                    +
                    t * (0x8f - 0x00)
                )

                g = (
                    0xa6
                    +
                    t * (0xab - 0xa6)
                )

                b = (
                    0xc8
                    +
                    t * (0xc4 - 0xc8)
                )

                pdf_canvas.setStrokeColor(
                    colors.Color(
                        r / 255,
                        g / 255,
                        b / 255
                    )
                )

                x0 = (
                    LEFT_MARGIN
                    +
                    (
                        AVAILABLE_WIDTH
                        * i
                        /
                        band_steps
                    )
                )

                x1 = (
                    LEFT_MARGIN
                    +
                    (
                        AVAILABLE_WIDTH
                        *
                        (i + 1)
                        /
                        band_steps
                    )
                )

                pdf_canvas.setLineWidth(
                    1.1
                )

                pdf_canvas.line(
                    x0,
                    band_y,
                    x1,
                    band_y
                )

            # -----------------------------------------------
            # CUSTOMER / DATE / INVOICE / T.O
            # -----------------------------------------------

            left_x = LEFT_MARGIN

            right_label_x = (
                PAGE_WIDTH
                - RIGHT_MARGIN
                - 48 * mm
            )

            row1_y = (
                band_y
                - 6.875 * mm
            )

            row2_y = (
                row1_y
                - 6.25 * mm
            )

            row3_y = (
                row2_y
                - 6.25 * mm
            )

            row4_y = (
                row3_y
                - 6.25 * mm
            )

            pdf_canvas.setFont(
                "Helvetica-Bold",
                9.4
            )

            pdf_canvas.setFillColor(
                MUTED
            )

            pdf_canvas.drawString(
                left_x,
                row1_y,
                "CUSTOMER NAME"
            )

            pdf_canvas.setFont(
                "Helvetica-Bold",
                13.1
            )

            pdf_canvas.setFillColor(
                INK
            )

            pdf_canvas.drawString(
                left_x,
                row2_y,
                str(branch)
            )

            # DATE

            pdf_canvas.setFont(
                "Helvetica-Bold",
                9.4
            )

            pdf_canvas.setFillColor(
                MUTED
            )

            pdf_canvas.drawString(
                right_label_x,
                row1_y,
                "DATE"
            )

            pdf_canvas.setFont(
                "Helvetica-Bold",
                10.6
            )

            pdf_canvas.setFillColor(
                INK
            )

            pdf_canvas.drawString(
                right_label_x + 20 * mm,
                row1_y,
                date_text_header
            )

            # INVOICE

            pdf_canvas.setFont(
                "Helvetica-Bold",
                9.4
            )

            pdf_canvas.setFillColor(
                MUTED
            )

            pdf_canvas.drawString(
                right_label_x,
                row2_y,
                "INVOICE #"
            )

            pdf_canvas.setFont(
                "Helvetica-Bold",
                10.6
            )

            pdf_canvas.setFillColor(
                INK
            )

            pdf_canvas.drawString(
                right_label_x + 20 * mm,
                row2_y,
                str(invoice_no)
            )

            # T.O #

            pdf_canvas.setFont(
                "Helvetica-Bold",
                9.4
            )

            pdf_canvas.setFillColor(
                MUTED
            )

            pdf_canvas.drawString(
                right_label_x,
                row3_y,
                "T.O #"
            )

            pdf_canvas.setFont(
                "Helvetica-Bold",
                8.75
            )

            pdf_canvas.setFillColor(
                INK
            )

            pdf_canvas.drawRightString(
                PAGE_WIDTH - RIGHT_MARGIN,
                row4_y,
                to_number_header
            )

        pdf_canvas.restoreState()

    # ========================================================
    # NUMBERED CANVAS
    # ========================================================

    from reportlab.pdfgen import canvas as reportlab_canvas

    class NumberedCanvas(
        reportlab_canvas.Canvas
    ):

        def __init__(
            self,
            *args,
            **kwargs
        ):

            reportlab_canvas.Canvas.__init__(
                self,
                *args,
                **kwargs
            )

            self._saved_page_states = []

        def showPage(self):

            self._saved_page_states.append(
                dict(self.__dict__)
            )

            self._startPage()

        def save(self):

            total_pages = len(
                self._saved_page_states
            )

            for state in self._saved_page_states:

                self.__dict__.update(
                    state
                )

                page_label = (
                    f"Page "
                    f"{self._pageNumber} "
                    f"of "
                    f"{total_pages}"
                )

                draw_letterhead(
                    self,
                    page_label,
                    self._pageNumber
                )

                reportlab_canvas.Canvas.showPage(
                    self
                )

            reportlab_canvas.Canvas.save(
                self
            )

    # ========================================================
    # TABLE COLUMNS
    # ========================================================

    columns = [
        ("S.No", None),
        ("Bar Code", None)
    ]

    if description_col:

        columns.append(
            ("Item Name", description_col)
        )

    if uom_col:

        columns.append(
            ("UoM", uom_col)
        )

    if quantity_col:

        columns.append(
            ("Qty", quantity_col)
        )

    if rate_col:

        columns.append(
            ("Rate", rate_col)
        )

    if amount_col:

        columns.append(
            ("Amount", amount_col)
        )

    numeric_display_names = [
        "Qty",
        "Rate",
        "Amount"
    ]

    center_display_names = [
        "S.No",
        "Bar Code",
        "UoM",
        "Qty",
        "Rate",
        "Amount"
    ]

    item_name_index = next(
        (
            i
            for i, (name, _)
            in enumerate(columns)
            if name == "Item Name"
        ),
        None
    )

    qty_index = next(
        (
            i
            for i, (name, _)
            in enumerate(columns)
            if name == "Qty"
        ),
        None
    )

    amount_index = next(
        (
            i
            for i, (name, _)
            in enumerate(columns)
            if name == "Amount"
        ),
        None
    )

    # ========================================================
    # FORMAT CELL
    # ========================================================

    def format_cell(
        display_name,
        original_col,
        row_number,
        row
    ):

        if display_name == "S.No":

            return str(row_number)

        if display_name == "Bar Code":

            return ""

        value = row.get(
            original_col,
            ""
        )

        if pd.isna(value):

            value = ""

        value = str(value)

        if display_name in numeric_display_names:

            try:

                number = float(
                    str(value)
                    .replace(",", "")
                    .strip()
                )

                if display_name == "Amount":

                    value = f"{number:,.0f}"

                else:

                    value = f"{number:,.2f}"

            except Exception:

                pass

        return (
            value
            .replace(
                "&",
                "&amp;"
            )
            .replace(
                "<",
                "&lt;"
            )
            .replace(
                ">",
                "&gt;"
            )
        )

    # ========================================================
    # TABLE HEADER
    #
    # repeatRows=1 below means this row automatically appears
    # at the top of EVERY page.
    # ========================================================

    table_data = [[

        Paragraph(
            str(display_name),
            (
                header_left_style
                if display_name == "Item Name"
                else header_style
            )
        )

        for display_name, _
        in columns

    ]]

    # ========================================================
    # DATA ROWS
    # ========================================================

    for row_number, (_, row) in enumerate(
        df.iterrows(),
        start=1
    ):

        pdf_row = []

        for display_name, original_col in columns:

            value = format_cell(
                display_name,
                original_col,
                row_number,
                row
            )

            if (
                display_name
                in numeric_display_names
            ):

                pdf_row.append(
                    Paragraph(
                        value,
                        center_style
                    )
                )

            elif (
                display_name
                in center_display_names
            ):

                pdf_row.append(
                    Paragraph(
                        value,
                        center_style
                    )
                )

            else:

                pdf_row.append(
                    Paragraph(
                        value,
                        normal_style
                    )
                )

        table_data.append(
            pdf_row
        )

    item_row_count = (
        len(table_data) - 1
    )

    # ========================================================
    # TOTALS
    # ========================================================

    total_quantity = (

        pd.to_numeric(
            df[quantity_col],
            errors="coerce"
        )
        .fillna(0)
        .sum()

        if quantity_col

        else None
    )

    total_amount = (

        pd.to_numeric(
            df[amount_col],
            errors="coerce"
        )
        .fillna(0)
        .sum()

        if amount_col

        else None
    )

    total_row = [
        ""
        for _
        in columns
    ]

    total_label_index = (
        item_name_index
        if item_name_index is not None
        else 0
    )

    total_row[
        total_label_index
    ] = Paragraph(
        "TOTAL",
        total_label_style
    )

    if (
        qty_index is not None
        and total_quantity is not None
    ):

        total_row[
            qty_index
        ] = Paragraph(
            f"{total_quantity:,.2f}",
            total_value_style
        )

    if (
        amount_index is not None
        and total_amount is not None
    ):

        total_row[
            amount_index
        ] = Paragraph(
            f"{total_amount:,.0f}",
            total_value_style
        )

    total_row = [

        cell
        if isinstance(
            cell,
            Paragraph
        )

        else Paragraph(
            "",
            normal_style
        )

        for cell in total_row

    ]

    # ========================================================
    # SPACER
    # ========================================================

    spacer_row = [

        Paragraph(
            "",
            normal_style
        )

        for _
        in columns
    ]

    spacer_row_idx = len(
        table_data
    )

    table_data.append(
        spacer_row
    )

    table_data.append(
        total_row
    )

    total_row_idx = (
        len(table_data) - 1
    )

    # ========================================================
    # AUTO COLUMN WIDTH
    # ========================================================

    MIN_WIDTH = 13 * mm
    MAX_WIDTH = 115 * mm
    CHAR_WIDTH = 2.625 * mm

    column_widths = []

    WIDTH_BOOST = {
        "UoM": 1.50,
        "Qty": 1.50,
        "Rate": 1.10,
        "Amount": 1.50,
    }

    for display_name, original_col in columns:

        longest_text = len(
            display_name
        )

        if display_name == "S.No":

            longest_text = max(
                longest_text,
                len(str(item_row_count))
            )

        elif display_name == "Bar Code":

            longest_text = max(
                longest_text,
                len("Bar Code")
            )

        elif display_name == "Amount":

            if original_col:

                for value in df[
                    original_col
                ].tolist():

                    if pd.isna(value):

                        continue

                    try:

                        number = float(
                            str(value)
                            .replace(",", "")
                            .strip()
                        )

                        text = (
                            f"{number:,.0f}"
                        )

                    except Exception:

                        text = str(value)

                    longest_text = max(
                        longest_text,
                        min(
                            len(text),
                            60
                        )
                    )

            if total_amount is not None:

                longest_text = max(
                    longest_text,
                    len(
                        f"{total_amount:,.0f}"
                    )
                )

        elif (
            display_name == "Qty"
            and total_quantity is not None
        ):

            longest_text = max(
                longest_text,
                len(
                    f"{total_quantity:,.2f}"
                )
            )

            for value in df[
                original_col
            ].tolist():

                if pd.isna(value):

                    continue

                try:

                    number = float(
                        str(value)
                        .replace(",", "")
                        .strip()
                    )

                    text = (
                        f"{number:,.2f}"
                    )

                except Exception:

                    text = str(value)

                longest_text = max(
                    longest_text,
                    min(
                        len(text),
                        60
                    )
                )

        elif original_col is not None:

            for value in df[
                original_col
            ].tolist():

                if pd.isna(value):

                    continue

                text = str(value)

                if (
                    display_name
                    in numeric_display_names
                ):

                    try:

                        number = float(
                            str(text)
                            .replace(",", "")
                            .strip()
                        )

                        text = (
                            f"{number:,.2f}"
                        )

                    except Exception:

                        pass

                longest_text = max(
                    longest_text,
                    min(
                        len(text),
                        60
                    )
                )

        width = max(
            longest_text * CHAR_WIDTH,
            MIN_WIDTH
        )

        width = min(
            width,
            MAX_WIDTH
        )

        width *= WIDTH_BOOST.get(
            display_name,
            1.0
        )

        column_widths.append(
            width
        )

    # ========================================================
    # SCALE TABLE
    # ========================================================

    protected_names = (
        "S.No",
        "Bar Code"
    )

    protected_total = sum(
        w
        for (
            display_name, _
        ),
        w
        in zip(
            columns,
            column_widths
        )
        if display_name
        in protected_names
    )

    scalable_total = sum(
        w
        for (
            display_name, _
        ),
        w
        in zip(
            columns,
            column_widths
        )
        if display_name
        not in protected_names
    )

    remaining_available = (
        AVAILABLE_WIDTH
        - protected_total
    )

    if (
        scalable_total > 0
        and remaining_available > 0
    ):

        scale = (
            remaining_available
            /
            scalable_total
        )

        column_widths = [

            w
            if display_name
            in protected_names

            else w * scale

            for (
                display_name, _
            ),
            w
            in zip(
                columns,
                column_widths
            )

        ]

    # ========================================================
    # TABLE
    # ========================================================

    invoice_table = Table(
        table_data,
        colWidths=column_widths,

        # ====================================================
        # VERY IMPORTANT:
        # Header row repeats on every physical page.
        # ====================================================

        repeatRows=1,

        hAlign="LEFT"
    )

    table_style_commands = [

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            HEADER_BG
        ),

        (
            "TEXTCOLOR",
            (0, 0),
            (-1, 0),
            colors.white
        ),

        (
            "FONTNAME",
            (0, 0),
            (-1, 0),
            "Helvetica-Bold"
        ),

        (
            "LINEBELOW",
            (0, 0),
            (-1, 0),
            1.4,
            ACCENT
        ),

        # ----------------------------------------------------
        # GRID
        # ----------------------------------------------------

        (
            "GRID",
            (0, 0),
            (-1, spacer_row_idx - 1),
            0.4,
            LINE_SOFT
        ),

        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE"
        ),

        # ----------------------------------------------------
        # PADDING
        # ----------------------------------------------------

        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            5
        ),

        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            5
        ),

        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            4
        ),

        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            4
        ),

        # ----------------------------------------------------
        # ALTERNATING ROWS
        # ----------------------------------------------------

        (
            "ROWBACKGROUNDS",
            (0, 1),
            (-1, spacer_row_idx - 1),
            [
                colors.white,
                ROW_ALT_BG
            ]
        ),

        # ----------------------------------------------------
        # SPACER
        # ----------------------------------------------------

        (
            "BACKGROUND",
            (0, spacer_row_idx),
            (-1, spacer_row_idx),
            colors.white
        ),

        (
            "TOPPADDING",
            (0, spacer_row_idx),
            (-1, spacer_row_idx),
            1.9
        ),

        (
            "BOTTOMPADDING",
            (0, spacer_row_idx),
            (-1, spacer_row_idx),
            1.9
        ),

        # ----------------------------------------------------
        # TOTAL
        # ----------------------------------------------------

        (
            "BACKGROUND",
            (0, total_row_idx),
            (-1, total_row_idx),
            TOTAL_BG
        ),

        (
            "LINEABOVE",
            (0, total_row_idx),
            (-1, total_row_idx),
            1.2,
            ACCENT_DARK
        ),

        (
            "BOX",
            (0, total_row_idx),
            (-1, total_row_idx),
            0.6,
            LINE
        ),

        (
            "TOPPADDING",
            (0, total_row_idx),
            (-1, total_row_idx),
            5.6
        ),

        (
            "BOTTOMPADDING",
            (0, total_row_idx),
            (-1, total_row_idx),
            5.6
        ),
    ]

    invoice_table.setStyle(
        TableStyle(
            table_style_commands
        )
    )

    # ========================================================
    # DOCUMENT
    #
    # The first-page margin is used while building the story.
    # Later pages are manually repositioned by the page template
    # below.
    # ========================================================

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,

        # First page needs room for the complete letterhead.
        topMargin=FIRST_PAGE_TOP_MARGIN,

        bottomMargin=BOTTOM_MARGIN
    )

    story = [
        invoice_table
    ]

    # ========================================================
    # BUILD
    #
    # Page 1 has the large letterhead area.
    #
    # Page 2+ uses a very small top margin. This is the key
    # change that makes the repeated column header start near
    # the top of the page, immediately below "Page X of Y".
    # ========================================================

    class InvoiceDocTemplate(SimpleDocTemplate):

        def handle_pageBegin(self):

            page_num = self.page

            if page_num == 1:

                self.topMargin = (
                    FIRST_PAGE_TOP_MARGIN
                )

            else:

                self.topMargin = (
                    OTHER_PAGE_TOP_MARGIN
                )

            self._handle_pageBegin()

    # Recreate using the custom document class
    doc = InvoiceDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=FIRST_PAGE_TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN
    )

    doc.build(
        story,
        canvasmaker=NumberedCanvas
    )

    buffer.seek(0)

    return buffer.getvalue()


# ============================================================
# GENERATE INVOICE FILES
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

        safe_branch = safe_filename(
            branch
        )

        safe_invoice = safe_filename(
            invoice_no
        )

        if pd.notna(invoice_date):

            date_text = (
                pd.Timestamp(
                    invoice_date
                ).strftime(
                    "%d-%b-%Y"
                )
            )

        else:

            date_text = "Unknown-Date"

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

                zip_path = (
                    f"{zip_root_folder}/"
                    f"{invoice['filename']}"
                )

                zip_file.writestr(
                    zip_path,
                    invoice["data"]
                )

        zip_buffer.seek(0)

        zip_filename = (
            f"{zip_root_folder}.zip"
        )

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
                    label="⬇️ Download as ZIP",
                    data=zip_buffer.getvalue(),
                    file_name=zip_filename,
                    mime="application/zip",
                    use_container_width=True
                )

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
                "**one folder containing every invoice PDF**. "
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
                    "Branch": invoice["branch"],
                    "Date": invoice["date"],
                    "Invoice No": invoice["invoice_no"],
                    "PDF File": invoice["filename"]
                }
            )

        generated_df = pd.DataFrame(
            generated_data
        )

        render_styled_table(
            generated_df,
            height=400,
            center_columns=[
                "Branch",
                "Date",
                "Invoice No"
            ],
            left_columns=[
                "PDF File"
            ],
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
