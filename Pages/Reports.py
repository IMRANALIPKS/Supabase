import streamlit as st
import pandas as pd

from io import BytesIO
import zipfile

from st_aggrid import AgGrid, DataReturnMode
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import JsCode

from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak

# ============================================================
# SUPABASE / NEON DATABASE CONNECTION
# ============================================================
from db import get_engine


# ============================================================
# PAGE SETTINGS
# ============================================================

st.set_page_config(page_title="supply_sheet", layout="wide")


# ============================================================
# FULL WIDTH / MINIMIZE LEFT & RIGHT SPACE
# ============================================================

st.markdown("""
<style>
.stAppViewContainer .main .block-container {
    max-width: 100% !important;
    width: 95% !important;
    padding-left: 0.15rem !important;
    padding-right: 0.15rem !important;
}
[data-testid="stMainBlockContainer"] {
    max-width: 100% !important;
    width: 95% !important;
    padding-left: 0.15rem !important;
    padding-right: 0.15rem !important;
}
.block-container { max-width: 100% !important; width: 95% !important; }

iframe[title*="agGrid"] { width: 100% !important; max-width: 100% !important; }
.ag-root-wrapper { width: 100% !important; max-width: 100% !important; }

.ag-cell { font-size: 12px !important; }
.ag-header-cell-text { font-size: 12px !important; }

.stTextInput { width: 100% !important; }
div[data-testid="stDataFrame"] { width: 100% !important; }
.ag-body-horizontal-scroll { height: 14px !important; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# VISUAL THEME
# ============================================================

def apply_elegant_theme():
    st.markdown(
        """
        <style>
        :root {
            --od-ink: #102033; --od-muted: #5d6f86; --od-line: #c4d7eb;
            --od-soft: #f3f8ff; --od-panel: #ffffff; --od-accent: #00a6c8;
            --od-accent-dark: #075e7a; --od-gold: #d69b2d;
        }
        .stApp {
            background:
                radial-gradient(circle at 12% 8%, rgba(0,166,200,.16), transparent 28%),
                radial-gradient(circle at 86% 6%, rgba(69,94,181,.14), transparent 26%),
                linear-gradient(180deg, #f6fbff 0%, #eaf3fb 48%, #f7f9fc 100%);
            color: var(--od-ink);
            font-family: "Segoe UI", "Inter", "Aptos", "Calibri", sans-serif;
        }
        .block-container { padding-top: 0.75rem; padding-bottom: 0.75rem; max-width: 100%; }
        iframe[title*="agGrid"] { height: calc(100vh - 320px) !important; min-height: 420px; }
        h1, h2, h3 {
            font-family: "Segoe UI Semibold", "Segoe UI", "Inter", sans-serif;
            letter-spacing: 0; color: var(--od-ink);
            text-shadow: 0 1px 0 rgba(255,255,255,.85), 0 -1px 0 rgba(16,32,51,.15);
        }
        [data-testid="stMetric"] {
            background: linear-gradient(180deg, #ffffff 0%, #eaf6ff 40%, #cde3f5 100%);
            border: 1px solid var(--od-line); border-radius: 10px; padding: 16px 18px;
            box-shadow:
                0 2px 0 rgba(255,255,255,1) inset,
                0 -3px 4px rgba(16,48,82,.16) inset,
                0 1px 0 #ffffff, 0 4px 0 #93b8d6, 0 18px 32px rgba(16,48,82,.26);
            transition: transform .12s ease, box-shadow .12s ease;
        }
        [data-testid="stMetric"]:hover {
            transform: translateY(-3px);
            box-shadow:
                0 2px 0 rgba(255,255,255,1) inset,
                0 -3px 4px rgba(16,48,82,.16) inset,
                0 1px 0 #ffffff, 0 6px 0 #93b8d6, 0 22px 36px rgba(16,48,82,.30);
        }
        [data-testid="stMetricLabel"] {
            color: var(--od-muted); font-weight: 600; text-transform: uppercase;
            letter-spacing: .06em; text-shadow: 0 1px 0 rgba(255,255,255,.9);
        }
        [data-testid="stMetricValue"] {
            color: var(--od-ink); font-weight: 600;
            text-shadow: 0 1px 0 rgba(255,255,255,.9), 0 2px 3px rgba(16,48,82,.18);
        }

        /* =====================================================
           3D INPUT STYLE — shared by search box, date range,
           and dropdown (multiselect / selectbox) cells
           ===================================================== */

        .stTextInput input,
        .stTextArea textarea,
        [data-testid="stDateInput"] input,
        [data-testid="stMultiSelect"] > div > div,
        [data-testid="stSelectbox"] > div > div {
            border: 1px solid #8fabc4 !important;
            border-radius: 9px !important;
            background: linear-gradient(180deg, #e4eff8 0%, #ffffff 26%) !important;
            box-shadow:
                inset 0 3px 6px rgba(16,32,51,.26),
                inset 0 -2px 0 rgba(255,255,255,.95),
                0 1px 0 rgba(255,255,255,.9) !important;
            font-family: "Segoe UI", "Aptos", "Calibri", sans-serif;
            font-weight: 700; color: var(--od-ink);
            text-shadow: 0 1px 0 rgba(255,255,255,.6);
        }
        .stTextInput input, .stTextArea textarea {
            padding-top: 10px; padding-bottom: 10px;
        }
        .stTextInput input:focus,
        .stTextArea textarea:focus,
        [data-testid="stDateInput"] input:focus,
        [data-testid="stMultiSelect"] > div > div:focus-within,
        [data-testid="stSelectbox"] > div > div:focus-within {
            border-color: var(--od-accent) !important;
            box-shadow:
                inset 0 3px 7px rgba(16,32,51,.32),
                inset 0 -2px 0 rgba(255,255,255,.95),
                0 0 0 3px rgba(0,166,200,.25) !important;
        }
        .stTextInput label, .stTextArea label,
        [data-testid="stDateInput"] label,
        [data-testid="stMultiSelect"] label,
        [data-testid="stSelectbox"] label {
            font-weight: 600; color: var(--od-ink);
        }
        [data-testid="stMultiSelect"] span[data-baseweb="tag"] {
    background: linear-gradient(180deg, #35d5ec 0%, #0d8bac 100%) !important;
    color: #102033 !important;

    box-shadow:
        inset 0 1px 0 rgba(255,255,255,.5),
        0 1px 2px rgba(16,48,82,.3) !important;
}

[data-testid="stMultiSelect"] span[data-baseweb="tag"] * {
    color: #102033 !important;
}

        .stButton > button, .stDownloadButton > button {
            border-radius: 7px; border: 1px solid #7fa5c3;
            background: linear-gradient(180deg, #ffffff 0%, #d9f1ff 52%, #bfdff2 100%);
            color: var(--od-ink); font-weight: 700;
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,.98),
                inset 0 -2px 0 rgba(16,48,82,.16),
                0 2px 0 #7fa5c3, 0 8px 16px rgba(16,48,82,.18);
        }
        .stButton > button[kind="primary"] {
            border-color: var(--od-accent-dark);
            background: linear-gradient(180deg, #35d5ec 0%, #0d8bac 48%, #075e7a 100%);
            color: #ffffff;
        }
        [data-testid="stCheckbox"] {
            background: linear-gradient(180deg, #ffffff 0%, #eaf6ff 100%);
            border: 1px solid #a9c6e0; border-radius: 7px; padding: 6px 10px;
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,.95),
                inset 0 -2px 0 rgba(16,48,82,.12),
                0 2px 0 #a9c6e0, 0 5px 10px rgba(16,48,82,.14);
            display: inline-block;
        }
        [data-testid="stCheckbox"] label p { font-weight: 600; color: var(--od-ink); }
        div[data-testid="stDataFrame"] {
            border: 1px solid #92b8d8; border-radius: 8px;
            box-shadow:
                0 2px 0 rgba(255,255,255,1) inset,
                0 -3px 5px rgba(16,48,82,.14) inset,
                0 4px 0 #93b8d6, 0 12px 22px rgba(16,48,82,.20);
            overflow: hidden;
        }
        hr { border-color: #d7e0ea; margin-top: 0.75rem; margin-bottom: 0.75rem; }
        </style>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM supply_sheet ORDER BY id", conn)

    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime("%Y-%m-%d")
        elif df[col].dtype == "object":
            non_null = df[col].dropna()
            if len(non_null) and non_null.apply(lambda v: hasattr(v, "isoformat")).all():
                df[col] = df[col].apply(lambda v: v.isoformat() if pd.notna(v) else v)

    return df


# ============================================================
# COLUMN DETECTION
# ============================================================

def _find_default_col(cols, exact_names, contains=None):
    lower_cols = {c.lower(): c for c in cols}
    for name in exact_names:
        if name.lower() in lower_cols:
            return lower_cols[name.lower()]
    if contains:
        contains_lower = contains.lower()
        for c in cols:
            if contains_lower in c.lower():
                return c
    return None


# ============================================================
# BUILD DISPLAY DATA WITH BRANCH / DAY / GRAND TOTALS
# ============================================================

def build_display_with_totals(data_df, branch_col, date_col, qty_col, amount_col):
    if data_df.empty or not branch_col:
        out = data_df.copy()
        out["_row_type"] = "data"
        return out

    cols = list(data_df.columns)
    out_rows = []
    grand_qty = 0.0
    grand_amt = 0.0

    for branch_val, branch_group in data_df.groupby(branch_col, sort=False, dropna=False):
        branch_qty = 0.0
        branch_amt = 0.0

        if date_col:
            date_groups = branch_group.groupby(date_col, sort=False, dropna=False)
        else:
            date_groups = [(None, branch_group)]

        for date_val, date_group in date_groups:
            for _, r in date_group.iterrows():
                row_dict = r.to_dict()
                row_dict["_row_type"] = "data"
                out_rows.append(row_dict)

            day_qty = (
                pd.to_numeric(date_group[qty_col], errors="coerce").fillna(0).sum()
                if qty_col else 0.0
            )
            day_amt = (
                pd.to_numeric(date_group[amount_col], errors="coerce").fillna(0).sum()
                if amount_col else 0.0
            )
            branch_qty += day_qty
            branch_amt += day_amt

            day_total_row = {c: None for c in cols}
            if date_col:
                day_total_row[date_col] = "Day Total"
            else:
                day_total_row[branch_col] = "Day Total"
            if qty_col:
                day_total_row[qty_col] = day_qty
            if amount_col:
                day_total_row[amount_col] = day_amt
            day_total_row["_row_type"] = "daytotal"
            out_rows.append(day_total_row)

        grand_qty += branch_qty
        grand_amt += branch_amt

        branch_total_row = {c: None for c in cols}
        branch_total_row[branch_col] = (
            "Blank Branch Total" if pd.isna(branch_val) else f"{branch_val} Total"
        )
        if qty_col:
            branch_total_row[qty_col] = branch_qty
        if amount_col:
            branch_total_row[amount_col] = branch_amt
        branch_total_row["_row_type"] = "subtotal"
        out_rows.append(branch_total_row)

        blank_branch_row = {c: None for c in cols}
        blank_branch_row["_row_type"] = "blank"
        out_rows.append(blank_branch_row)

    grand_row = {c: None for c in cols}
    grand_row[branch_col] = "Grand Total"
    if qty_col:
        grand_row[qty_col] = grand_qty
    if amount_col:
        grand_row[amount_col] = grand_amt
    grand_row["_row_type"] = "grandtotal"
    out_rows.append(grand_row)

    return pd.DataFrame(out_rows)


def prepare_report_csv(data_df):
    csv_df = data_df.copy()
    hidden_columns = ["_row_type", "id"]
    csv_df = csv_df.drop(
        columns=[c for c in hidden_columns if c in csv_df.columns], errors="ignore"
    )
    csv_df = csv_df.rename(
        columns={c: str(c).replace("_", " ").title() for c in csv_df.columns}
    )
    return csv_df


# ============================================================
# PDF GENERATION
# ============================================================

def _branch_pdf_table(branch_df, date_col, qty_col, amount_col):
    """Build a reportlab Table (data rows + Day Total rows + a Branch Total row) for one branch."""

    display_cols = [c for c in branch_df.columns if c not in ("id", "_row_type")]

    if date_col and date_col in branch_df.columns:
        branch_df = branch_df.sort_values(by=date_col, na_position="last")

    table_data = [[str(c).replace("_", " ").title() for c in display_cols]]
    row_types = ["header"]

    date_groups = (
        branch_df.groupby(date_col, sort=False, dropna=False)
        if date_col and date_col in branch_df.columns else [(None, branch_df)]
    )

    branch_qty = 0.0
    branch_amt = 0.0

    for _, date_group in date_groups:
        for _, r in date_group.iterrows():
            table_data.append(["" if pd.isna(r[c]) else str(r[c]) for c in display_cols])
            row_types.append("data")

        day_qty = pd.to_numeric(date_group[qty_col], errors="coerce").fillna(0).sum() if qty_col else 0.0
        day_amt = pd.to_numeric(date_group[amount_col], errors="coerce").fillna(0).sum() if amount_col else 0.0
        branch_qty += day_qty
        branch_amt += day_amt

        day_row = ["" for _ in display_cols]
        if date_col in display_cols:
            day_row[display_cols.index(date_col)] = "Day Total"
        if qty_col in display_cols:
            day_row[display_cols.index(qty_col)] = f"{day_qty:,.2f}"
        if amount_col in display_cols:
            day_row[display_cols.index(amount_col)] = f"{day_amt:,.0f}"
        table_data.append(day_row)
        row_types.append("daytotal")

    total_row = ["" for _ in display_cols]
    label_col = date_col if date_col in display_cols else display_cols[0]
    total_row[display_cols.index(label_col)] = "Branch Total"
    if qty_col in display_cols:
        total_row[display_cols.index(qty_col)] = f"{branch_qty:,.2f}"
    if amount_col in display_cols:
        total_row[display_cols.index(amount_col)] = f"{branch_amt:,.0f}"
    table_data.append(total_row)
    row_types.append("total")

    table = Table(table_data, repeatRows=1)

    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b7795")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c4d7eb")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]

    for i, rtype in enumerate(row_types):
        if rtype == "daytotal":
            style_cmds += [
                ("BACKGROUND", (0, i), (-1, i), colors.HexColor("#e5fbff")),
                ("FONTNAME", (0, i), (-1, i), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, i), (-1, i), colors.HexColor("#075e7a")),
            ]
        elif rtype == "total":
            style_cmds += [
                ("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fff2cc")),
                ("FONTNAME", (0, i), (-1, i), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, i), (-1, i), colors.HexColor("#5c3d00")),
            ]
        elif rtype == "data" and i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f4fbff")))

    table.setStyle(TableStyle(style_cmds))
    return table


def _pdf_styles():
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ODTitle", parent=styles["Title"], textColor=colors.HexColor("#102b4e"), fontSize=18, spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        "ODSubtitle", parent=styles["Normal"], textColor=colors.HexColor("#5d6f86"), fontSize=10, spaceAfter=4
    )
    branch_heading_style = ParagraphStyle(
        "ODBranchHeading", parent=styles["Heading2"], textColor=colors.HexColor("#0b7795"), fontSize=14, spaceAfter=6
    )
    return title_style, subtitle_style, branch_heading_style


def generate_branch_pdf(branch_name, branch_df, date_col, qty_col, amount_col, date_range_label=""):
    """One PDF for a single branch."""

    title_style, subtitle_style, _ = _pdf_styles()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=portrait(A4),
        leftMargin=24, rightMargin=24, topMargin=28, bottomMargin=24
    )

    story = [
        Paragraph("OD Pakistan - Supply Sheet", title_style),
        Paragraph(f"Branch Report: {branch_name}", subtitle_style),
    ]
    if date_range_label:
        story.append(Paragraph(date_range_label, subtitle_style))
    story.append(Spacer(1, 8))
    story.append(_branch_pdf_table(branch_df, date_col, qty_col, amount_col))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_combined_pdf(branches, report_df, branch_col, date_col, qty_col, amount_col, date_range_label=""):
    """One PDF containing every selected branch, each as its own section (page break between)."""

    title_style, subtitle_style, branch_heading_style = _pdf_styles()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=portrait(A4),
        leftMargin=24, rightMargin=24, topMargin=28, bottomMargin=24
    )

    story = [
        Paragraph("OD Pakistan - Supply Sheet", title_style),
        Paragraph("All Branches Report", subtitle_style),
    ]
    if date_range_label:
        story.append(Paragraph(date_range_label, subtitle_style))
    story.append(Spacer(1, 10))

    for i, branch_name in enumerate(branches):
        branch_df = report_df[report_df[branch_col] == branch_name].copy()
        if branch_df.empty:
            continue

        if i > 0:
            story.append(PageBreak())

        story.append(Paragraph(str(branch_name), branch_heading_style))
        story.append(_branch_pdf_table(branch_df, date_col, qty_col, amount_col))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# SHARED AG GRID JS (read-only report grid styling)
# ============================================================

row_style_js = JsCode(
    """
    function(params) {
        if (!params.data) { return {}; }
        if (params.data._row_type === 'daytotal') {
            return {
                'fontWeight': 'bold', 'backgroundColor': '#e5fbff', 'color': '#075e7a',
                'borderTop': '1px solid #8fd8e5', 'borderBottom': '1px solid #bdeaf1'
            };
        }
        if (params.data._row_type === 'subtotal') {
            return {
                'fontWeight': 'bold', 'backgroundColor': '#e8f0ff', 'color': '#17366d',
                'borderTop': '2px solid #5f8ee8', 'borderBottom': '2px solid #5f8ee8'
            };
        }
        if (params.data._row_type === 'grandtotal') {
            return {
                'fontWeight': 'bold', 'backgroundColor': '#fff2cc', 'color': '#5c3d00',
                'borderTop': '3px solid #d69b2d', 'borderBottom': '4px double #d69b2d'
            };
        }
        if (params.data._row_type === 'blank') {
            return { 'height': '12px', 'backgroundColor': '#f8fafc' };
        }
        if (params.node && params.node.rowIndex % 2 === 1) {
            return { 'backgroundColor': '#f4fbff' };
        }
        return { 'backgroundColor': '#ffffff' };
    }
    """
)

cell_style_js = JsCode(
    """
    function(params) {
        if (params.data && params.data._row_type === 'data') {
            return {
                'fontFamily': 'Segoe UI, Aptos, Calibri, sans-serif', 'fontWeight': '600',
                'color': '#1f2937',
                'borderRight': '1px solid #b9d2e8', 'borderBottom': '1px solid #b9d2e8',
                'boxShadow':
                    'inset 0 1px 0 rgba(255,255,255,.9), ' +
                    'inset 0 -3px 4px rgba(16,48,82,.16), ' +
                    'inset -2px 0 3px rgba(16,48,82,.08)',
                'textShadow': '0 1px 0 rgba(255,255,255,.7)'
            };
        }
        return {
            'fontFamily': 'Segoe UI, Aptos, Calibri, sans-serif',
            'borderRight': '1px solid #aac6e0', 'borderBottom': '1px solid #aac6e0',
            'boxShadow':
                'inset 0 1px 0 rgba(255,255,255,.85), ' +
                'inset 0 -2px 3px rgba(16,48,82,.12)'
        };
    }
    """
)

numeric_cell_style_js = JsCode(
    """
    function(params) {
        if (params.data && params.data._row_type === 'data') {
            return {
                'textAlign': 'center', 'fontFamily': 'Segoe UI, Aptos, Calibri, sans-serif',
                'fontWeight': '600', 'color': '#1f2937',
                'borderRight': '1px solid #b9d2e8', 'borderBottom': '1px solid #b9d2e8',
                'boxShadow':
                    'inset 0 1px 0 rgba(255,255,255,.9), ' +
                    'inset 0 -3px 4px rgba(16,48,82,.16), ' +
                    'inset -2px 0 3px rgba(16,48,82,.08)',
                'textShadow': '0 1px 0 rgba(255,255,255,.7)'
            };
        }
        return {
            'textAlign': 'center', 'fontFamily': 'Segoe UI, Aptos, Calibri, sans-serif',
            'boxShadow':
                'inset 0 1px 0 rgba(255,255,255,.85), ' +
                'inset 0 -2px 3px rgba(16,48,82,.12)'
        };
    }
    """
)

decimal_value_formatter_js = JsCode(
    """
    function(params) {
        var v = params.value;
        if (v === null || v === undefined || v === '') { return ''; }
        var num = Number(v);
        if (isNaN(num)) { return v; }
        if (num === 0) { return '-'; }
        return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
    """
)

amount_value_formatter_js = JsCode(
    """
    function(params) {
        var v = params.value;
        if (v === null || v === undefined || v === '') { return ''; }
        var num = Number(v);
        if (isNaN(num)) { return v; }
        if (num === 0) { return '-'; }
        return num.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
    }
    """
)

grid_custom_css = {
    ".ag-root-wrapper": {
        "border": "1px solid #92b8d8 !important", "border-radius": "8px !important",
        "box-shadow": "0 18px 34px rgba(16,48,82,.18), inset 0 1px 0 #ffffff !important",
        "overflow": "hidden !important"
    },
    ".ag-header": {
        "background": "linear-gradient(180deg, #0b7795 0%, #102b4e 100%) !important",
        "border-bottom": "2px solid #38d5ec !important"
    },
    ".ag-header-cell": {
        "border-right": "1px solid rgba(255,255,255,.22) !important",
        "box-shadow": "inset 2px 2px 0 rgba(255,255,255,.38), inset -2px -2px 3px rgba(0,0,0,.38) !important"
    },
    ".ag-header-cell-label": {
        "font-family": "Segoe UI, Aptos, Calibri, sans-serif !important",
        "font-weight": "600 !important", "justify-content": "center !important"
    },
    ".ag-header-cell-text": {
        "font-family": "Segoe UI, Aptos, Calibri, sans-serif !important",
        "font-weight": "600 !important", "color": "#ffffff !important",
        "font-size": "12px !important", "text-transform": "uppercase !important",
        "text-shadow": "0 1px 1px rgba(0,0,0,.45) !important"
    },
    ".ag-cell": {
        "border-color": "#d7e7f5 !important",
        "border-left": "1px solid rgba(255,255,255,.95) !important",
        "border-top": "1px solid rgba(255,255,255,.92) !important",
        "font-size": "13px !important", "line-height": "34px !important",
        "padding-left": "9px !important", "padding-right": "9px !important"
    },
    ".ag-cell-focus": { "box-shadow": "inset 0 0 0 2px #38d5ec !important" },
    ".ag-row-hover": { "background-color": "#dcf7ff !important" },
    ".ag-row-selected": { "background-color": "#caeff8 !important" },
    ".ag-floating-filter-input": {
        "border-radius": "5px !important", "border": "1px solid #b8c6d6 !important",
        "box-shadow": "inset 0 1px 3px rgba(16,32,51,.18) !important"
    },
    ".ag-side-bar": { "border-left": "1px solid #cbd6e2 !important" }
}

column_widths = {
    "Branch": 180, "Date": 105, "Inv No": 115, "Inv #": 115,
    "Description": 280, "Item name": 280, "UOM": 70, "UoM": 70,
    "Quantity": 95, "Qty": 95, "Rate": 110, "T.O Rate": 110,
    "to_rate": 110, "Amount": 130
}


def build_report_grid_options(display_df, date_col):
    gb = GridOptionsBuilder.from_dataframe(display_df)

    gb.configure_default_column(
        cellStyle=cell_style_js,
        filter=True,
        floatingFilter=True,
        sortable=True,
        resizable=True,
        editable=False,
        minWidth=50,
        filterParams={"buttons": ["reset", "apply"], "defaultJoinOperator": "AND"},
        wrapText=False,
        autoHeight=False
    )

    gb.configure_column("_row_type", hide=True)

    if date_col and date_col in display_df.columns:
        gb.configure_column(date_col, cellDataType="text")

    if "id" in display_df.columns:
        gb.configure_column("id", hide=True)

    for col in display_df.columns:
        gb.configure_column(col, minWidth=50, resizable=True)

    for col, width in column_widths.items():
        if col in display_df.columns:
            gb.configure_column(col, width=width, minWidth=50, resizable=True)

    for wide_col, max_w in [("Description", 450), ("Item name", 450)]:
        if wide_col in display_df.columns:
            gb.configure_column(wide_col, width=280, minWidth=150, maxWidth=max_w, resizable=True)

    if "Branch" in display_df.columns:
        gb.configure_column("Branch", width=140, minWidth=100, maxWidth=250, resizable=True)

    for col in ["quantity", "qty", "rate", "to_rate", "amount"]:
        if col in display_df.columns:
            gb.configure_column(col, cellStyle=numeric_cell_style_js)

    for col in ["quantity", "qty", "rate", "to_rate"]:
        if col in display_df.columns:
            gb.configure_column(col, valueFormatter=decimal_value_formatter_js)

    if "amount" in display_df.columns:
        gb.configure_column("amount", valueFormatter=amount_value_formatter_js)

    gb.configure_side_bar(filters_panel=True, columns_panel=True)

    gb.configure_grid_options(
        enableRangeSelection=True,
        rowHeight=34,
        headerHeight=34,
        clipboardDelimiter="\t",
        getRowStyle=row_style_js,
        pagination=False,
        onFirstDataRendered=JsCode(
            """
            function(params) {
                setTimeout(function() {
                    var allColumnIds = [];
                    params.api.getColumns().forEach(function(column) {
                        var colId = column.getColId();
                        if (colId !== '_row_type' && colId !== 'id') {
                            allColumnIds.push(colId);
                        }
                    });
                    params.api.autoSizeColumns(allColumnIds, false);
                }, 300);
            }
            """
        )
    )

    return gb.build()


# ============================================================
# INITIAL DATA
# ============================================================

df = load_data()

branch_col = _find_default_col(list(df.columns), ["branch"], "branch")
date_col = _find_default_col(
    list(df.columns),
    ["date", "inv_date", "invoice_date", "order_date", "transaction_date"],
    "date"
)
description_col = _find_default_col(
    list(df.columns), ["description", "desc", "item_name", "item"], "desc"
)
qty_col = _find_default_col(list(df.columns), ["quantity", "qty"], "quantity")
amount_col = _find_default_col(list(df.columns), ["amount"], "amount")

_default_sort_cols = [c for c in [branch_col, date_col, description_col] if c]


# ============================================================
# TITLE
# ============================================================

apply_elegant_theme()
st.title("OD Pakistan - Supply Sheet")


# ============================================================
# REPORT
# ============================================================

st.subheader("📊 Branch & Date Report")

if not branch_col:
    st.warning("No branch column was found in this table, so branch-wise reporting isn't available.")
else:
    branch_options = sorted(df[branch_col].dropna().unique().tolist())

    rc1, rc2 = st.columns([2, 2])

    with rc1:
        all_branches = st.checkbox("All Branches", value=True, key="report_all_branches")

        if all_branches:
            selected_branches = branch_options
            st.multiselect(
                "Branches", options=branch_options, default=branch_options,
                disabled=True, key="report_branches_locked"
            )
        else:
            selected_branches = st.multiselect(
                "Select one or more branches", options=branch_options,
                default=branch_options[:1] if branch_options else [],
                key="report_branches"
            )

    with rc2:
        date_range = None
        if date_col and date_col in df.columns:
            parsed_dates = pd.to_datetime(df[date_col], errors="coerce")
            min_date, max_date = parsed_dates.min(), parsed_dates.max()

            if pd.notna(min_date) and pd.notna(max_date):
                date_range = st.date_input(
                    "Date range",
                    value=(min_date.date(), max_date.date()),
                    min_value=min_date.date(),
                    max_value=max_date.date(),
                    key="report_date_range"
                )
        else:
            st.caption("No date column detected — date filtering is unavailable.")

    report_df = df[df[branch_col].isin(selected_branches)].copy() if selected_branches else df.iloc[0:0].copy()

    if date_col and isinstance(date_range, tuple) and len(date_range) == 2:
        parsed = pd.to_datetime(report_df[date_col], errors="coerce")
        start, end = date_range
        report_df = report_df[(parsed.dt.date >= start) & (parsed.dt.date <= end)]

    if _default_sort_cols:
        report_df = report_df.sort_values(
            by=_default_sort_cols, ascending=True, na_position="last"
        ).reset_index(drop=True)

    rk1, rk2, rk3 = st.columns(3)

    with rk1:
        st.metric("Records", f"{len(report_df):,}")

    with rk2:
        rqty = pd.to_numeric(report_df[qty_col], errors="coerce").fillna(0).sum() if qty_col else 0
        st.metric("Total Quantity", f"{rqty:,.2f}")

    with rk3:
        ramt = pd.to_numeric(report_df[amount_col], errors="coerce").fillna(0).sum() if amount_col else 0
        st.metric("Total Amount", f"{ramt:,.2f}")

    if report_df.empty:
        st.info("No records match the selected branch(es)/date range.")
    else:
        report_display_df = build_display_with_totals(report_df, branch_col, date_col, qty_col, amount_col)

        report_grid_options = build_report_grid_options(report_display_df, date_col)

        AgGrid(
            report_display_df,
            gridOptions=report_grid_options,
            enable_enterprise_modules=False,
            height=650,
            fit_columns_on_grid_load=False,
            update_on=["filterChanged", "sortChanged"],
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            allow_unsafe_jscode=True,
            custom_css=grid_custom_css,
            key="report_grid"
        )

        st.divider()

        report_csv_df = prepare_report_csv(report_display_df)

        branch_tag = "all_branches" if all_branches else "_".join(
            str(b).strip().replace(" ", "-") for b in selected_branches
        )[:60] or "selection"

        date_range_label = (
            f"{date_range[0]} to {date_range[1]}"
            if date_col and isinstance(date_range, tuple) and len(date_range) == 2
            else "All dates"
        )

        pdf_branches = [b for b in selected_branches if b in report_df[branch_col].unique().tolist()]

        st.markdown("**Downloads**")
        rd1, rd2, rd3 = st.columns(3)

        with rd1:
            st.download_button(
                "📥 CSV",
                data=report_csv_df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"branch_report_{branch_tag}.csv",
                mime="text/csv",
                use_container_width=True
            )

        with rd2:
            if len(pdf_branches) <= 1:
                single_branch = pdf_branches[0] if pdf_branches else "Report"
                single_pdf_bytes = generate_branch_pdf(
                    single_branch,
                    report_df[report_df[branch_col] == single_branch].copy() if pdf_branches else report_df.copy(),
                    date_col, qty_col, amount_col, date_range_label
                )
                st.download_button(
                    "📥 PDF (Branch)",
                    data=single_pdf_bytes,
                    file_name=f"branch_report_{branch_tag}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                combined_pdf_bytes = generate_combined_pdf(
                    pdf_branches, report_df, branch_col, date_col, qty_col, amount_col, date_range_label
                )
                st.download_button(
                    "📥 PDF (All in One)",
                    data=combined_pdf_bytes,
                    file_name=f"branch_report_{branch_tag}_combined.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

        with rd3:
            if len(pdf_branches) > 1:
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for b in pdf_branches:
                        b_df = report_df[report_df[branch_col] == b].copy()
                        if b_df.empty:
                            continue
                        pdf_bytes = generate_branch_pdf(b, b_df, date_col, qty_col, amount_col, date_range_label)
                        safe_name = "".join(
                            ch if ch.isalnum() or ch in (" ", "-", "_") else "_" for ch in str(b)
                        ).strip().replace(" ", "_") or "branch"
                        zf.writestr(f"{safe_name}.pdf", pdf_bytes)
                zip_buffer.seek(0)

                st.download_button(
                    "📥 PDF (ZIP, Separate Files)",
                    data=zip_buffer.getvalue(),
                    file_name=f"branch_reports_{branch_tag}.zip",
                    mime="application/zip",
                    use_container_width=True
                )
