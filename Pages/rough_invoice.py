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

    return buffer