import streamlit as st
import pandas as pd
import psycopg2
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED

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
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background-color: #f5f7fa;
    }

    .main-title {
        font-size: 32px;
        font-weight: 800;
        color: #111827;
        margin-bottom: 3px;
    }

    .sub-title {
        color: #6b7280;
        font-size: 15px;
        margin-bottom: 20px;
    }

    .metric-card {
        background-color: white;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }

    .metric-title {
        font-size: 13px;
        color: #6b7280;
    }

    .metric-value {
        font-size: 25px;
        font-weight: 800;
        color: #111827;
    }

    </style>
    """,
    unsafe_allow_html=True
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
# KPI CARDS
# ============================================================

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">
                Total Invoices
            </div>
            <div class="metric-value">
                {invoice_count:,}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with col2:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">
                Branches
            </div>
            <div class="metric-value">
                {branch_count:,}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with col3:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">
                Records
            </div>
            <div class="metric-value">
                {record_count:,}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with col4:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">
                Grand Total
            </div>
            <div class="metric-value">
                Rs. {grand_total:,.0f}
            </div>
        </div>
        """,
        unsafe_allow_html=True
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


invoice_summary = (
    report_df
    .groupby(
        [
            "inv_date",
            "branch",
            "inv_no"
        ],
        as_index=False
    )
    .agg(
        records=("id", "count"),
        quantity=("quantity", "sum"),
        amount=("amount", "sum")
    )
    .sort_values(
        [
            "inv_date",
            "branch",
            "inv_no"
        ]
    )
)


preview = invoice_summary.copy()


preview["inv_date"] = (
    preview["inv_date"]
    .dt.strftime("%d-%b-%Y")
)


preview["quantity"] = (
    preview["quantity"]
    .map(
        lambda x: f"{x:,.2f}"
    )
)


preview["amount"] = (
    preview["amount"]
    .map(
        lambda x: f"Rs. {x:,.2f}"
    )
)


preview.columns = [
    "Date",
    "Branch",
    "Invoice No",
    "Records",
    "Quantity",
    "Amount"
]


st.dataframe(
    preview,
    use_container_width=True,
    hide_index=True,
    height=400
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

    buffer = BytesIO()

    # ========================================================
    # PAGE
    # ========================================================

    PAGE_WIDTH, PAGE_HEIGHT = A4

    LEFT_MARGIN = 8 * mm
    RIGHT_MARGIN = 8 * mm
    TOP_MARGIN = 8 * mm
    BOTTOM_MARGIN = 8 * mm

    AVAILABLE_WIDTH = (
        PAGE_WIDTH
        - LEFT_MARGIN
        - RIGHT_MARGIN
    )

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN
    )

    # ========================================================
    # STYLES
    # ========================================================

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=21,
        alignment=TA_CENTER,
        spaceAfter=3 * mm
    )

    header_style = ParagraphStyle(
        "HeaderStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=8,
        alignment=TA_CENTER
    )

    normal_style = ParagraphStyle(
        "NormalStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=8,
        alignment=TA_LEFT
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

    # ========================================================
    # STORY
    # ========================================================

    story = []

    # ========================================================
    # TITLE
    # ========================================================

    story.append(
        Paragraph(
            "OD PAKISTAN",
            title_style
        )
    )

    story.append(
        Paragraph(
            "SUPPLY SHEET / INVOICE",
            ParagraphStyle(
                "SubTitle",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=10,
                alignment=TA_CENTER,
                spaceAfter=3 * mm
            )
        )
    )

    # ========================================================
    # INVOICE INFORMATION
    # ========================================================

    info_data = [
        [
            Paragraph("<b>Branch:</b>", header_style),
            Paragraph(str(branch), normal_style),

            Paragraph("<b>Date:</b>", header_style),
            Paragraph(str(invoice_date), normal_style),

            Paragraph("<b>Invoice No:</b>", header_style),
            Paragraph(str(invoice_no), normal_style),
        ]
    ]

    info_table = Table(
        info_data,
        colWidths=[
            20 * mm,
            45 * mm,
            18 * mm,
            30 * mm,
            25 * mm,
            45 * mm
        ],
        hAlign="LEFT"
    )

    info_table.setStyle(
        TableStyle([
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.25,
                colors.lightgrey
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                4
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                4
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                3
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                3
            ),
        ])
    )

    story.append(info_table)
    story.append(Spacer(1, 4 * mm))

    # ========================================================
    # PREPARE DATA
    # ========================================================

    df = invoice_df.copy()

    # Remove completely empty rows
    df = df.dropna(how="all")

    # --------------------------------------------------------
    # COLUMN NAME DETECTION
    # --------------------------------------------------------

    def find_column(possible_names):

        for col in df.columns:

            clean_col = str(col).strip().lower()

            for name in possible_names:

                if name in clean_col:
                    return col

        return None

    branch_col = find_column([
        "branch"
    ])

    date_col = find_column([
        "date",
        "inv date",
        "invoice date"
    ])

    invoice_col = find_column([
        "inv #",
        "inv no",
        "invoice no",
        "invoice"
    ])

    description_col = find_column([
        "description",
        "particular",
        "item",
        "item name"
    ])

    uom_col = find_column([
        "uom",
        "unit"
    ])

    quantity_col = find_column([
        "quantity",
        "qty"
    ])

    rate_col = find_column([
        "rate"
    ])

    to_rate_col = find_column([
        "t.o rate",
        "to rate",
        "torate"
    ])

    amount_col = find_column([
        "amount",
        "total"
    ])

    # ========================================================
    # STANDARD COLUMN ORDER
    # ========================================================

    columns = []

    if branch_col:
        columns.append(("Branch", branch_col))

    if date_col:
        columns.append(("Date", date_col))

    if invoice_col:
        columns.append(("Inv #", invoice_col))

    if description_col:
        columns.append(("Description", description_col))

    if uom_col:
        columns.append(("UOM", uom_col))

    if quantity_col:
        columns.append(("Quantity", quantity_col))

    if rate_col:
        columns.append(("Rate", rate_col))

    if to_rate_col:
        columns.append(("T.O Rate", to_rate_col))

    if amount_col:
        columns.append(("Amount", amount_col))

    # If no recognized columns, use original columns
    if not columns:

        columns = [
            (str(col), col)
            for col in df.columns
        ]

    # ========================================================
    # HEADER
    # ========================================================

    table_data = []

    table_data.append([
        Paragraph(str(display_name), header_style)
        for display_name, original_col in columns
    ])

    # ========================================================
    # DATA ROWS
    # ========================================================

    for _, row in df.iterrows():

        pdf_row = []

        for display_name, original_col in columns:

            value = row.get(original_col, "")

            if pd.isna(value):
                value = ""

            value = str(value)

            # ------------------------------------------------
            # NUMBER FORMATTING
            # ------------------------------------------------

            if display_name in [
                "Quantity",
                "Rate",
                "T.O Rate",
                "Amount"
            ]:

                try:

                    number = float(
                        str(value)
                        .replace(",", "")
                        .strip()
                    )

                    value = f"{number:,.2f}"

                except:

                    pass

            # ------------------------------------------------
            # ESCAPE HTML
            # ------------------------------------------------

            value = (
                value
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )

            # ------------------------------------------------
            # ALIGNMENT
            # ------------------------------------------------

            if display_name in [
                "Quantity",
                "Rate",
                "T.O Rate",
                "Amount"
            ]:

                pdf_row.append(
                    Paragraph(
                        value,
                        right_style
                    )
                )

            elif display_name in [
                "Date",
                "Inv #",
                "UOM"
            ]:

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

        table_data.append(pdf_row)

    # ========================================================
    # AUTOFIT COLUMN WIDTHS
    # ========================================================

    # Minimum and maximum width for each column
    MIN_WIDTH = 12 * mm
    MAX_WIDTH = 70 * mm

    column_widths = []

    for col_index, (display_name, original_col) in enumerate(columns):

        # Start with header width
        longest_text = len(str(display_name))

        # Check actual content
        for value in df[original_col].tolist():

            if pd.isna(value):
                continue

            text = str(value)

            # Numeric values after formatting
            if display_name in [
                "Quantity",
                "Rate",
                "T.O Rate",
                "Amount"
            ]:

                try:

                    number = float(
                        str(text)
                        .replace(",", "")
                        .strip()
                    )

                    text = f"{number:,.2f}"

                except:

                    pass

            # Limit calculation length
            longest_text = max(
                longest_text,
                min(len(text), 45)
            )

        # Approximate character width
        width = (
            longest_text * 3.0 * mm
        )

        # Minimum
        width = max(
            width,
            MIN_WIDTH
        )

        # Maximum
        width = min(
            width,
            MAX_WIDTH
        )

        column_widths.append(width)

    # ========================================================
    # SCALE TO A4 PAGE WIDTH
    # ========================================================

    total_width = sum(column_widths)

    if total_width > AVAILABLE_WIDTH:

        scale = (
            AVAILABLE_WIDTH
            / total_width
        )

        column_widths = [
            width * scale
            for width in column_widths
        ]

    # ========================================================
    # DESCRIPTION GETS EXTRA SPACE
    # ========================================================

    if description_col:

        description_index = None

        for i, (display_name, original_col) in enumerate(columns):

            if original_col == description_col:

                description_index = i
                break

        if description_index is not None:

            # Give description more room
            extra_space = (
                AVAILABLE_WIDTH
                - sum(column_widths)
            )

            if extra_space > 0:

                column_widths[
                    description_index
                ] += extra_space

    # ========================================================
    # FINAL SAFETY CHECK
    # ========================================================

    total_width = sum(column_widths)

    if total_width > AVAILABLE_WIDTH:

        scale = (
            AVAILABLE_WIDTH
            / total_width
        )

        column_widths = [
            width * scale
            for width in column_widths
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

    invoice_table.setStyle(
        TableStyle([

            # ------------------------------------------------
            # HEADER
            # ------------------------------------------------

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#d9eaf7")
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.HexColor("#102033")
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            # ------------------------------------------------
            # GRID
            # ------------------------------------------------

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                colors.HexColor("#8fabc4")
            ),

            # ------------------------------------------------
            # ALIGNMENT
            # ------------------------------------------------

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            # ------------------------------------------------
            # PADDING
            # ------------------------------------------------

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                3
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                3
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                3
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                3
            ),

            # ------------------------------------------------
            # ALTERNATE ROW COLOR
            # ------------------------------------------------

            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#f5f9fc")
                ]
            ),

        ])
    )

    story.append(invoice_table)

    # ========================================================
    # TOTAL AMOUNT
    # ========================================================

    if amount_col:

        try:

            total_amount = (
                pd.to_numeric(
                    df[amount_col],
                    errors="coerce"
                )
                .fillna(0)
                .sum()
            )

            story.append(
                Spacer(1, 3 * mm)
            )

            total_data = [
                [
                    "",
                    Paragraph(
                        "<b>Grand Total</b>",
                        right_style
                    ),
                    Paragraph(
                        f"<b>{total_amount:,.2f}</b>",
                        right_style
                    )
                ]
            ]

            total_table = Table(
                total_data,
                colWidths=[
                    AVAILABLE_WIDTH * 0.55,
                    AVAILABLE_WIDTH * 0.20,
                    AVAILABLE_WIDTH * 0.25
                ],
                hAlign="RIGHT"
            )

            total_table.setStyle(
                TableStyle([
                    (
                        "BOX",
                        (1, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor("#8fabc4")
                    ),
                    (
                        "BACKGROUND",
                        (1, 0),
                        (-1, -1),
                        colors.HexColor("#e4eff8")
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE"
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
                ])
            )

            story.append(total_table)

        except Exception:
            pass

    # ========================================================
    # BUILD PDF
    # ========================================================

    doc.build(story)

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
        # PDF filename
        # ----------------------------------------------------

        if safe_invoice:

            filename = (
                f"{date_text}_"
                f"{safe_invoice}.pdf"
            )

        else:

            filename = (
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
        # ONLY ONE INVOICE
        # ====================================================

        if len(invoice_files) == 1:

            invoice = invoice_files[0]

            st.download_button(
                label="⬇️ Download Invoice PDF",
                data=invoice["data"],
                file_name=invoice["filename"],
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )


        # ====================================================
        # MULTIPLE INVOICES → ZIP
        # ====================================================

        else:

            zip_buffer = BytesIO()


            with ZipFile(
                zip_buffer,
                "w",
                ZIP_DEFLATED
            ) as zip_file:

                for invoice in invoice_files:

                    # ------------------------------------------------
                    # IMPORTANT:
                    #
                    # ZIP structure:
                    #
                    # Branch/
                    #     Date_InvoiceNo.pdf
                    #
                    # No date subfolder.
                    # ------------------------------------------------

                    zip_path = (
                        f"{invoice['branch']}/"
                        f"{invoice['filename']}"
                    )


                    zip_file.writestr(
                        zip_path,
                        invoice["data"]
                    )


            zip_buffer.seek(0)


            # ----------------------------------------------------
            # ZIP NAME
            # ----------------------------------------------------

            zip_filename = (
                "OD_PAKISTAN_Invoices_"
                f"{start_date.strftime('%Y%m%d')}_"
                f"{end_date.strftime('%Y%m%d')}.zip"
            )


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
                "**Branch → Individual Invoice PDFs**. "
                "The invoice date is included in each PDF filename."
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


        st.dataframe(
            generated_df,
            use_container_width=True,
            hide_index=True,
            height=400
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