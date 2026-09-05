import streamlit as st
import pandas as pd

from psycopg2.extras import execute_values
from io import StringIO
from datetime import datetime

from st_aggrid import AgGrid, DataReturnMode
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import JsCode

from db import get_engine, get_conn


# ============================================================
# PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="OD Pakistan - Supply Sheet",
    layout="wide"
)


# ============================================================
# PAGE CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background:
            radial-gradient(
                circle at 12% 8%,
                rgba(0,166,200,.16),
                transparent 28%
            ),
            radial-gradient(
                circle at 86% 6%,
                rgba(69,94,181,.14),
                transparent 26%
            ),
            linear-gradient(
                180deg,
                #f6fbff 0%,
                #eaf3fb 48%,
                #f7f9fc 100%
            );

        color:#102033;

        font-family:
            "Segoe UI",
            "Inter",
            "Aptos",
            "Calibri",
            sans-serif;
    }

    .block-container {
        max-width:100% !important;
        width:95% !important;
        padding-left:.15rem !important;
        padding-right:.15rem !important;
        padding-top:.75rem;
        padding-bottom:.75rem;
    }

    iframe[title*="agGrid"] {
        width:100% !important;
        max-width:100% !important;
        height:calc(100vh - 320px) !important;
        min-height:420px;
    }

    .ag-root-wrapper {
        width:100% !important;
        max-width:100% !important;
    }

    .ag-cell {
        font-size:13px !important;
    }

    .ag-header-cell-text {
        font-size:12px !important;
    }

    .stTextInput input,
    .stTextArea textarea,
    .stDateInput input,
    .stMultiSelect [data-baseweb="select"] > div,
    .stSelectbox [data-baseweb="select"] > div {
        border:1px solid #8fabc4;
        border-radius:9px;

        background:
            linear-gradient(
                180deg,
                #e4eff8 0%,
                #ffffff 26%
            );

        box-shadow:
            inset 0 3px 6px rgba(16,32,51,.26),
            inset 0 -2px 0 rgba(255,255,255,.95),
            0 1px 0 rgba(255,255,255,.9);

        font-family:
            "Segoe UI",
            "Aptos",
            "Calibri",
            sans-serif;

        font-weight:600;
        color:#102033;
    }

    .stTextInput input:focus,
    .stTextArea textarea:focus {
        border-color:#00a6c8;

        box-shadow:
            inset 0 3px 7px rgba(16,32,51,.32),
            inset 0 -2px 0 rgba(255,255,255,.95),
            0 0 0 3px rgba(0,166,200,.25);
    }

    .stButton > button,
    .stDownloadButton > button {
        border-radius:7px;
        border:1px solid #7fa5c3;

        background:
            linear-gradient(
                180deg,
                #ffffff 0%,
                #d9f1ff 52%,
                #bfdff2 100%
            );

        color:#102033;
        font-weight:700;

        box-shadow:
            inset 0 1px 0 rgba(255,255,255,.98),
            inset 0 -2px 0 rgba(16,48,82,.16),
            0 2px 0 #7fa5c3,
            0 8px 16px rgba(16,48,82,.18);
    }

    .stButton > button[kind="primary"] {
        border-color:#075e7a;

        background:
            linear-gradient(
                180deg,
                #35d5ec 0%,
                #0d8bac 48%,
                #075e7a 100%
            );

        color:#ffffff;
    }

    [data-testid="stExpander"] {
        border:1px solid #92b8d8 !important;
        border-radius:10px !important;

        background:
            linear-gradient(
                180deg,
                #ffffff 0%,
                #eef6fc 100%
            ) !important;

        box-shadow:
            0 2px 0 rgba(255,255,255,1) inset,
            0 -3px 5px rgba(16,48,82,.14) inset,
            0 4px 0 #93b8d6,
            0 14px 26px rgba(16,48,82,.22) !important;

        overflow:hidden;
    }

    div[data-testid="stDataFrame"] {
        border:1px solid #92b8d8;
        border-radius:8px;

        box-shadow:
            0 2px 0 rgba(255,255,255,1) inset,
            0 -3px 5px rgba(16,48,82,.14) inset,
            0 4px 0 #93b8d6,
            0 12px 22px rgba(16,48,82,.20);

        overflow:hidden;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
    }

    .stTabs [data-baseweb="tab"] {
        border:1px solid #8fabc4;
        border-radius:8px 8px 0 0;
        background:
            linear-gradient(180deg, #ffffff 0%, #e4eff8 100%);
        font-weight:600;
        padding:6px 14px;
    }

    hr {
        border-color:#d7e0ea;
        margin-top:.75rem;
        margin-bottom:.75rem;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# CTRL + S
# ============================================================

def enable_ctrl_s_save():

    st.components.v1.html(
        """
        <script>

        (function() {

            const doc = window.parent.document;

            if (window.parent.__odSupplyCtrlSBound) {
                return;
            }

            window.parent.__odSupplyCtrlSBound = true;

            doc.addEventListener(
                'keydown',
                function(e) {

                    const key = e.key
                        ? e.key.toLowerCase()
                        : '';

                    if (
                        (e.ctrlKey || e.metaKey)
                        && key === 's'
                    ) {

                        e.preventDefault();

                        const buttons =
                            Array.from(
                                doc.querySelectorAll('button')
                            );

                        const saveBtn =
                            buttons.find(
                                b =>
                                b.innerText &&
                                b.innerText.includes(
                                    'Save Additions / Amendments'
                                )
                            );

                        if (saveBtn) {
                            saveBtn.click();
                        }
                    }

                },
                true
            );

        })();

        </script>
        """,
        height=1
    )


# ============================================================
# DATABASE COLUMN INFORMATION
# ============================================================

@st.cache_data(ttl=30)
def get_table_columns():

    conn = get_conn()

    try:

        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                column_name,
                ordinal_position,
                data_type,
                is_nullable,
                is_generated,
                identity_generation
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'supply_sheet'
            ORDER BY ordinal_position
            """
        )

        rows = cur.fetchall()

        cur.close()

    finally:

        conn.close()

    if not rows:

        raise RuntimeError(
            "Table 'supply_sheet' was not found "
            "in the public schema."
        )

    columns = []

    for row in rows:

        columns.append(
            {
                "name": row[0],
                "position": row[1],
                "data_type": row[2],
                "nullable": row[3],
                "generated": row[4],
                "identity": row[5]
            }
        )

    return columns


# ============================================================
# READ TABLE STRUCTURE
# ============================================================

try:

    column_info = get_table_columns()

except Exception as e:

    st.error(
        f"Unable to read Supabase table structure: {e}"
    )

    st.stop()


all_db_columns = [
    x["name"]
    for x in column_info
]


# ============================================================
# IMPORTANT COLUMN CLASSIFICATION
#
# id:
#     hidden but used for UPDATE / DELETE
#
# identity:
#     hidden internal database columns
#
# generated:
#     VISIBLE, but NOT EDITABLE
# ============================================================

hidden_internal_columns = []

generated_columns = []

identity_columns = []


for info in column_info:

    col = info["name"]

    if col.lower() == "id":

        hidden_internal_columns.append(col)

        continue

    if info["identity"] is not None:

        identity_columns.append(col)

        hidden_internal_columns.append(col)

        continue

    if info["generated"] == "ALWAYS":

        generated_columns.append(col)


# ============================================================
# REMOVE S.NO IF IT EXISTS
# ============================================================

visible_columns = []

for col in all_db_columns:

    if col.lower() in (
        "id",
        "s.no",
        "s_no",
        "serial_no",
        "serial number"
    ):

        continue

    visible_columns.append(col)


# ============================================================
# FIND COLUMN
# ============================================================

def find_column_name(columns, names):

    lower_map = {
        c.lower(): c
        for c in columns
    }

    for name in names:

        if name.lower() in lower_map:

            return lower_map[name.lower()]

    return None


barcode_col = find_column_name(
    visible_columns,
    ["barcode", "bar_code", "bar code"]
)


to_no_col = find_column_name(
    visible_columns,
    [
        "to_no", "to no", "t.o #", "t.o no",
        "t.o.", "to#", "tono"
    ]
)


ordered_columns = []

if barcode_col:
    ordered_columns.append(barcode_col)

if to_no_col and to_no_col not in ordered_columns:
    ordered_columns.append(to_no_col)

for col in visible_columns:
    if col not in ordered_columns:
        ordered_columns.append(col)

visible_columns = ordered_columns


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data(ttl=30)
def load_data():

    engine = get_engine()

    with engine.connect() as conn:

        df = pd.read_sql(
            """
            SELECT *
            FROM supply_sheet
            ORDER BY id
            """,
            conn
        )

    return df


try:

    df = load_data()

except Exception as e:

    st.error(
        f"Unable to load supply_sheet: {e}"
    )

    st.stop()


for col in all_db_columns:

    if col not in df.columns:

        df[col] = None


internal_existing = []

for col in hidden_internal_columns:

    if col in df.columns:

        internal_existing.append(col)


df = df[
    internal_existing
    +
    [c for c in visible_columns if c in df.columns]
]


# ============================================================
# DATE CONVERSION
# ============================================================

for col in df.columns:

    if pd.api.types.is_datetime64_any_dtype(df[col]):

        df[col] = df[col].dt.strftime("%Y-%m-%d")

    elif df[col].dtype == "object":

        non_null = df[col].dropna()

        if len(non_null):

            try:

                if non_null.apply(
                    lambda v: hasattr(v, "isoformat")
                ).all():

                    df[col] = df[col].apply(
                        lambda v:
                        v.isoformat()
                        if pd.notna(v)
                        else v
                    )

            except Exception:

                pass


# ============================================================
# ENTRY COLUMNS
# ============================================================

entry_columns = [
    c
    for c in visible_columns
    if c not in generated_columns
]


numeric_entry_cols = []

for info in column_info:

    col = info["name"]

    if col not in entry_columns:
        continue

    data_type = info["data_type"].lower()

    if data_type in (
        "smallint", "integer", "bigint",
        "numeric", "decimal", "real", "double precision"
    ):

        numeric_entry_cols.append(col)


# ============================================================
# NUMERIC / VALUE HELPERS
# ============================================================

def clean_numeric_value(val):

    if val is None:
        return None

    if isinstance(val, float) and pd.isna(val):
        return None

    s = str(val).strip()

    if s == "":
        return None

    if s.lower() in ("nan", "none", "null"):
        return None

    s = s.replace(",", "")

    try:
        return float(s)
    except (ValueError, TypeError):
        return s


def normalize_value(val, is_numeric=False):

    if val is None:
        return None

    try:
        if pd.isna(val):
            return None
    except Exception:
        pass

    if is_numeric:

        cleaned = clean_numeric_value(val)

        if cleaned is None:
            return None

        if isinstance(cleaned, (int, float)):
            return round(float(cleaned), 6)

        return cleaned

    value = str(val).strip()

    return value if value else None


def find_by_names(columns, exact_names, contains=None):

    lower_cols = {c.lower(): c for c in columns}

    for name in exact_names:

        if name.lower() in lower_cols:
            return lower_cols[name.lower()]

    if contains:

        contains_lower = contains.lower()

        for c in columns:
            if contains_lower in c.lower():
                return c

    return None


# ============================================================
# COMMON COLUMN IDENTIFICATION (needed for filters/sort/totals)
# ============================================================

branch_col = find_by_names(
    list(df.columns), ["branch"], "branch"
)

date_col = find_by_names(
    list(df.columns),
    ["date", "inv_date", "invoice_date", "order_date", "transaction_date"],
    "date"
)

description_col = find_by_names(
    list(df.columns),
    ["description", "desc", "item_name", "item"],
    "desc"
)

qty_col = find_by_names(
    list(df.columns), ["quantity", "qty"], "quantity"
)

amount_col = find_by_names(
    list(df.columns), ["amount"], "amount"
)


# ============================================================
# SESSION STATE
# ============================================================

if "new_rows_df" not in st.session_state:

    st.session_state.new_rows_df = pd.DataFrame(columns=entry_columns)

if "filter_branches" not in st.session_state:

    st.session_state.filter_branches = []

if "filter_date_range" not in st.session_state:

    st.session_state.filter_date_range = ()


# ============================================================
# TITLE
# ============================================================

title_col, refresh_col = st.columns([6, 1])

with title_col:

    st.title("OD Pakistan - Supply Sheet")

with refresh_col:

    st.write("")

    if st.button("🔄 Refresh Data", use_container_width=True):

        load_data.clear()
        get_table_columns.clear()

        st.rerun()

enable_ctrl_s_save()


# ============================================================
# DATA ENTRY
# ============================================================

with st.expander("➕ Data Entry — Add New Rows", expanded=False):

    entry_tab_add, entry_tab_quick = st.tabs(
        ["📋 Add Multiple Rows", "🖊️ Quick Add (Single Row)"]
    )

    # --------------------------------------------------------
    # TAB 1: ADD MULTIPLE ROWS (PASTE OR FILE UPLOAD)
    # --------------------------------------------------------

    with entry_tab_add:

        add_method = st.radio(
            "How do you want to add rows?",
            options=["Paste from Excel", "Upload CSV / Excel File"],
            horizontal=True,
            key="add_method_radio"
        )

        if add_method == "Paste from Excel":

            st.caption(
                "Paste data in this exact column order: "
                + " → ".join(entry_columns)
            )

            pasted_text = st.text_area(
                "Paste Excel data here",
                height=160,
                key="paste_box",
                placeholder="Copy rows from Excel and paste here..."
            )

            p1, p2, p3 = st.columns(3)

            with p1:
                append_mode_paste = st.checkbox(
                    "Append to staged rows", value=True, key="append_paste"
                )

            with p2:
                load_clicked = st.button("⬆️ Load Pasted Rows", key="load_pasted")

            with p3:
                clear_clicked_paste = st.button(
                    "🗑️ Clear Staged Rows", key="clear_staged_paste"
                )

            if clear_clicked_paste:

                st.session_state.new_rows_df = pd.DataFrame(columns=entry_columns)
                st.rerun()

            if load_clicked:

                if not pasted_text.strip():

                    st.warning("Paste box is empty.")

                else:

                    try:

                        parsed = pd.read_csv(
                            StringIO(pasted_text),
                            sep="\t",
                            header=None,
                            dtype=str
                        )

                        parsed = parsed.dropna(how="all")

                        if parsed.shape[1] > len(entry_columns):

                            st.warning(
                                f"Excel contains {parsed.shape[1]} columns, "
                                f"but only {len(entry_columns)} input columns "
                                f"are required. Extra columns were ignored."
                            )

                            parsed = parsed.iloc[:, :len(entry_columns)]

                        elif parsed.shape[1] < len(entry_columns):

                            missing = len(entry_columns) - parsed.shape[1]

                            for _ in range(missing):
                                parsed[parsed.shape[1]] = None

                        parsed.columns = entry_columns

                        for col in numeric_entry_cols:

                            if col in parsed.columns:
                                parsed[col] = parsed[col].apply(clean_numeric_value)

                        if append_mode_paste:

                            st.session_state.new_rows_df = pd.concat(
                                [st.session_state.new_rows_df, parsed],
                                ignore_index=True
                            )

                        else:

                            st.session_state.new_rows_df = parsed.reset_index(drop=True)

                        st.success(f"{len(parsed):,} row(s) staged successfully.")

                        st.rerun()

                    except Exception as e:

                        st.error(f"Could not parse pasted data: {e}")

        else:

            st.caption(
                "Upload a .csv or .xlsx file. If the file's headers match the "
                "database column names they will be matched automatically; "
                "otherwise columns are mapped in order: "
                + " → ".join(entry_columns)
            )

            uploaded_file = st.file_uploader(
                "Choose a CSV or Excel file",
                type=["csv", "xlsx", "xls"],
                key="entry_file_uploader"
            )

            u1, u2 = st.columns(2)

            with u1:
                append_mode_file = st.checkbox(
                    "Append to staged rows", value=True, key="append_file"
                )

            with u2:
                load_file_clicked = st.button(
                    "⬆️ Load File Rows", key="load_file_rows"
                )

            if load_file_clicked:

                if uploaded_file is None:

                    st.warning("Please choose a file first.")

                else:

                    try:

                        if uploaded_file.name.lower().endswith(".csv"):

                            file_df = pd.read_csv(uploaded_file, dtype=str)

                        else:

                            file_df = pd.read_excel(uploaded_file, dtype=str)

                        file_df = file_df.dropna(how="all")

                        # Try to match headers case-insensitively first
                        lower_entry_map = {c.lower(): c for c in entry_columns}

                        header_matches = [
                            col for col in file_df.columns
                            if str(col).strip().lower() in lower_entry_map
                        ]

                        if len(header_matches) >= max(1, len(entry_columns) // 2):

                            rename_map = {
                                col: lower_entry_map[str(col).strip().lower()]
                                for col in file_df.columns
                                if str(col).strip().lower() in lower_entry_map
                            }

                            file_df = file_df.rename(columns=rename_map)

                            for col in entry_columns:

                                if col not in file_df.columns:
                                    file_df[col] = None

                            file_df = file_df[entry_columns]

                        else:

                            if file_df.shape[1] > len(entry_columns):

                                file_df = file_df.iloc[:, :len(entry_columns)]

                            elif file_df.shape[1] < len(entry_columns):

                                missing = len(entry_columns) - file_df.shape[1]

                                for _ in range(missing):
                                    file_df[file_df.shape[1]] = None

                            file_df.columns = entry_columns

                        for col in numeric_entry_cols:

                            if col in file_df.columns:
                                file_df[col] = file_df[col].apply(clean_numeric_value)

                        if append_mode_file:

                            st.session_state.new_rows_df = pd.concat(
                                [st.session_state.new_rows_df, file_df],
                                ignore_index=True
                            )

                        else:

                            st.session_state.new_rows_df = file_df.reset_index(drop=True)

                        st.success(f"{len(file_df):,} row(s) staged from file.")

                        st.rerun()

                    except Exception as e:

                        st.error(f"Could not read uploaded file: {e}")

    # --------------------------------------------------------
    # TAB 2: QUICK ADD SINGLE ROW
    # --------------------------------------------------------

    with entry_tab_quick:

        st.caption("Fill in the fields below to stage a single new row.")

        with st.form("quick_add_form", clear_on_submit=True):

            quick_values = {}

            form_cols = st.columns(2)

            for idx, col in enumerate(entry_columns):

                target_col = form_cols[idx % 2]

                with target_col:

                    if col in numeric_entry_cols:

                        quick_values[col] = st.number_input(
                            col, value=0.0, step=1.0, key=f"quick_{col}"
                        )

                    elif col == date_col:

                        quick_values[col] = st.date_input(
                            col, value=datetime.today(), key=f"quick_{col}"
                        )

                    else:

                        quick_values[col] = st.text_input(
                            col, key=f"quick_{col}"
                        )

            quick_submit = st.form_submit_button("➕ Add Row to Staged List")

            if quick_submit:

                row_dict = {}

                for col in entry_columns:

                    val = quick_values.get(col)

                    if col == date_col and val is not None:
                        val = val.strftime("%Y-%m-%d")

                    row_dict[col] = val

                new_row = pd.DataFrame([row_dict])

                st.session_state.new_rows_df = pd.concat(
                    [st.session_state.new_rows_df, new_row],
                    ignore_index=True
                )

                st.success("Row staged. Scroll down and click "
                            "'Save Additions / Amendments' to write it "
                            "to the database.")

                st.rerun()

    # --------------------------------------------------------
    # STAGED ROWS PREVIEW (shared across all 3 tabs)
    # --------------------------------------------------------

    if len(st.session_state.new_rows_df):

        st.divider()

        st.write(
            f"**{len(st.session_state.new_rows_df):,} row(s) waiting to be saved:**"
        )

        st.dataframe(
            st.session_state.new_rows_df,
            use_container_width=True,
            height=220
        )

        clear_all_staged = st.button("🗑️ Clear All Staged Rows", key="clear_all_staged")

        if clear_all_staged:

            st.session_state.new_rows_df = pd.DataFrame(columns=entry_columns)
            st.rerun()


st.divider()


# ============================================================
# SEARCH & FILTERS
# ============================================================

st.subheader("🔍 Search & Filter")

search_row1, search_row2, search_row3, search_row4 = st.columns([3, 2, 2, 1])

with search_row1:

    search = st.text_input(
        "Quick Search — searches all columns", key="quick_search_box"
    )

with search_row2:

    if branch_col and branch_col in df.columns:

        branch_options = sorted(
            [
                b for b in df[branch_col].dropna().unique().tolist()
            ]
        )

        selected_branches = st.multiselect(
            "Filter by Branch",
            options=branch_options,
            default=st.session_state.filter_branches,
            key="branch_filter_select"
        )

    else:

        selected_branches = []

with search_row3:

    if date_col and date_col in df.columns:

        date_series = pd.to_datetime(df[date_col], errors="coerce").dropna()

        if len(date_series):

            min_date = date_series.min().date()
            max_date = date_series.max().date()

            date_filter_value = st.date_input(
                "Filter by Date Range",
                value=(),
                min_value=min_date,
                max_value=max_date,
                key="date_range_filter"
            )

        else:

            date_filter_value = ()

    else:

        date_filter_value = ()

with search_row4:

    st.write("")

    reset_filters_clicked = st.button("♻️ Reset", use_container_width=True)

if reset_filters_clicked:

    for key in (
        "quick_search_box",
        "branch_filter_select",
        "date_range_filter"
    ):

        if key in st.session_state:
            del st.session_state[key]

    st.rerun()


# ============================================================
# APPLY FILTERS + SEARCH
# ============================================================

view_df = df.copy()

if selected_branches and branch_col:

    view_df = view_df[view_df[branch_col].isin(selected_branches)]

if (
    date_col
    and isinstance(date_filter_value, tuple)
    and len(date_filter_value) == 2
):

    start_d, end_d = date_filter_value

    date_parsed = pd.to_datetime(view_df[date_col], errors="coerce")

    view_df = view_df[
        (date_parsed.dt.date >= start_d)
        & (date_parsed.dt.date <= end_d)
    ]

if search:

    search_text = search.strip()

    if search_text:

        mask = (
            view_df
            .astype(str)
            .apply(
                lambda row: row.str.contains(
                    search_text, case=False, na=False, regex=False
                ),
                axis=1
            )
            .any(axis=1)
        )

        view_df = view_df[mask]


# ============================================================
# DEFAULT SORT (Branch → Date → Description, ascending)
# ============================================================

sort_columns = []

for col in [branch_col, date_col, description_col]:

    if col and col in view_df.columns and col not in sort_columns:

        sort_columns.append(col)

if sort_columns:

    view_df = (
        view_df
        .sort_values(by=sort_columns, ascending=True, na_position="last")
        .reset_index(drop=True)
    )


# ============================================================
# SUMMARY VALUES
# ============================================================

if qty_col:

    qty = pd.to_numeric(view_df[qty_col], errors="coerce").fillna(0).sum()

else:

    qty = 0

if amount_col:

    amt = pd.to_numeric(view_df[amount_col], errors="coerce").fillna(0).sum()

else:

    amt = 0


# ============================================================
# SUMMARY CARDS
# ============================================================

card_style = """
height:58px;
padding:5px 10px;
box-sizing:border-box;
text-align:center;

border:1px solid #8fabc4;
border-radius:9px;

background:
linear-gradient(
    180deg,
    #e4eff8 0%,
    #ffffff 26%
);

box-shadow:
inset 0 3px 6px rgba(16,32,51,.26),
inset 0 -2px 0 rgba(255,255,255,.95),
0 1px 0 rgba(255,255,255,.9);

font-family:
"Segoe UI",
"Aptos",
"Calibri",
sans-serif;
"""


col1, col2, col3 = st.columns(3)

with col1:

    st.html(
        f"""
        <div style="{card_style}">
            <div style="font-size:11px;font-weight:600;color:#30465a;line-height:15px;">
                Records
            </div>
            <div style="font-size:20px;font-weight:700;color:#102033;line-height:25px;">
                {len(view_df):,}
            </div>
        </div>
        """
    )

with col2:

    st.html(
        f"""
        <div style="{card_style}">
            <div style="font-size:11px;font-weight:600;color:#30465a;line-height:15px;">
                Total Quantity
            </div>
            <div style="font-size:20px;font-weight:700;color:#102033;line-height:25px;">
                {qty:,.2f}
            </div>
        </div>
        """
    )

with col3:

    st.html(
        f"""
        <div style="{card_style}">
            <div style="font-size:11px;font-weight:600;color:#30465a;line-height:15px;">
                Total Amount
            </div>
            <div style="font-size:20px;font-weight:700;color:#102033;line-height:25px;">
                {amt:,.2f}
            </div>
        </div>
        """
    )


# ============================================================
# BUILD DISPLAY DATA WITH TOTALS
# ============================================================

def build_display_with_totals(
    data_df, branch_col, date_col, qty_col, amount_col
):

    if data_df.empty:

        out = data_df.copy()
        out["_row_type"] = "data"
        return out

    if not branch_col:

        out = data_df.copy()
        out["_row_type"] = "data"
        return out

    cols = list(data_df.columns)

    out_rows = []

    grand_qty = 0.0
    grand_amt = 0.0

    for branch_val, branch_group in data_df.groupby(
        branch_col, sort=False, dropna=False
    ):

        branch_qty = 0.0
        branch_amt = 0.0

        if date_col:

            date_groups = branch_group.groupby(
                date_col, sort=False, dropna=False
            )

        else:

            date_groups = [(None, branch_group)]

        for date_val, date_group in date_groups:

            for _, r in date_group.iterrows():

                row_dict = r.to_dict()
                row_dict["_row_type"] = "data"
                out_rows.append(row_dict)

            if qty_col:

                day_qty = pd.to_numeric(
                    date_group[qty_col], errors="coerce"
                ).fillna(0).sum()

            else:

                day_qty = 0.0

            if amount_col:

                day_amt = pd.to_numeric(
                    date_group[amount_col], errors="coerce"
                ).fillna(0).sum()

            else:

                day_amt = 0.0

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

        if pd.isna(branch_val):
            branch_total_row[branch_col] = "Blank Branch Total"
        else:
            branch_total_row[branch_col] = f"{branch_val} Total"

        if qty_col:
            branch_total_row[qty_col] = branch_qty

        if amount_col:
            branch_total_row[amount_col] = branch_amt

        branch_total_row["_row_type"] = "subtotal"

        out_rows.append(branch_total_row)

        blank_row = {c: None for c in cols}
        blank_row["_row_type"] = "blank"

        out_rows.append(blank_row)

    grand_row = {c: None for c in cols}
    grand_row[branch_col] = "Grand Total"

    if qty_col:
        grand_row[qty_col] = grand_qty

    if amount_col:
        grand_row[amount_col] = grand_amt

    grand_row["_row_type"] = "grandtotal"

    out_rows.append(grand_row)

    return pd.DataFrame(out_rows)


display_df = build_display_with_totals(
    view_df, branch_col, date_col, qty_col, amount_col
)


display_columns = []

for col in internal_existing:

    if col in display_df.columns:
        display_columns.append(col)

for col in visible_columns:

    if col in display_df.columns:
        display_columns.append(col)

if "_row_type" in display_df.columns:
    display_columns.append("_row_type")

display_df = display_df[display_columns]


# ============================================================
# AG GRID
# ============================================================

gb = GridOptionsBuilder.from_dataframe(display_df)

row_editable_js = JsCode(
    """
    function(params) {
        return (
            params.data &&
            params.data._row_type === 'data'
        );
    }
    """
)

row_style_js = JsCode(
    """
    function(params) {

        if (!params.data) {
            return {};
        }

        if (params.data._row_type === 'daytotal') {
            return {
                'fontWeight': 'bold',
                'backgroundColor': '#e5fbff',
                'color': '#075e7a',
                'borderTop': '1px solid #8fd8e5',
                'borderBottom': '1px solid #bdeaf1'
            };
        }

        if (params.data._row_type === 'subtotal') {
            return {
                'fontWeight': 'bold',
                'backgroundColor': '#e8f0ff',
                'color': '#17366d',
                'borderTop': '2px solid #5f8ee8',
                'borderBottom': '2px solid #5f8ee8'
            };
        }

        if (params.data._row_type === 'grandtotal') {
            return {
                'fontWeight': 'bold',
                'backgroundColor': '#fff2cc',
                'color': '#5c3d00',
                'borderTop': '3px solid #d69b2d',
                'borderBottom': '4px double #d69b2d'
            };
        }

        if (params.data._row_type === 'blank') {
            return {
                'height': '12px',
                'backgroundColor': '#f8fafc'
            };
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
        return {
            'fontFamily': 'Segoe UI, Aptos, Calibri, sans-serif',
            'fontWeight': '600',
            'color': '#1f2937',
            'borderRight': '1px solid #b9d2e8',
            'borderBottom': '1px solid #b9d2e8',
            'boxShadow':
                'inset 0 1px 0 rgba(255,255,255,.9), ' +
                'inset 0 -3px 4px rgba(16,48,82,.16), ' +
                'inset -2px 0 3px rgba(16,48,82,.08)',
            'textShadow': '0 1px 0 rgba(255,255,255,.7)'
        };
    }
    """
)

gb.configure_default_column(
    cellStyle=cell_style_js,
    filter=True,
    floatingFilter=True,
    sortable=True,
    resizable=True,
    editable=row_editable_js,
    minWidth=50,
    filterParams={
        "buttons": ["reset", "apply"],
        "defaultJoinOperator": "AND"
    },
    wrapText=False,
    autoHeight=False
)

gb.configure_column("_row_type", hide=True, suppressColumnsToolPanel=True)

for col in hidden_internal_columns:

    if col in display_df.columns:

        gb.configure_column(
            col, hide=True, editable=False, suppressColumnsToolPanel=True
        )

for col in generated_columns:

    if col in display_df.columns:

        gb.configure_column(
            col, editable=False, hide=False, suppressColumnsToolPanel=False
        )

column_widths = {
    "branch": 140, "Branch": 140,
    "date": 105, "Date": 105,
    "inv_no": 115, "Inv No": 115, "Inv #": 115,
    "invoice_no": 120,
    "barcode": 130, "Barcode": 130,
    "to_no": 110, "T.O #": 110,
    "description": 280, "Description": 280,
    "item_name": 280, "Item name": 280,
    "uom": 70, "UOM": 70, "UoM": 70,
    "quantity": 95, "Quantity": 95, "qty": 95, "Qty": 95,
    "rate": 110, "Rate": 110,
    "to_rate": 110, "T.O Rate": 110,
    "amount": 130, "Amount": 130
}

for col, width in column_widths.items():

    if col in display_df.columns:

        gb.configure_column(col, width=width, minWidth=50, resizable=True)

for col in ["Description", "description", "Item name", "item_name"]:

    if col in display_df.columns:

        gb.configure_column(
            col, width=280, minWidth=150, maxWidth=450, resizable=True
        )

for col in ["Branch", "branch"]:

    if col in display_df.columns:

        gb.configure_column(
            col, width=140, minWidth=100, maxWidth=250, resizable=True
        )

numeric_cell_style_js = JsCode(
    """
    function(params) {
        return {
            'textAlign': 'center',
            'fontFamily': 'Segoe UI, Aptos, Calibri, sans-serif',
            'fontWeight': '600',
            'color': '#1f2937',
            'borderRight': '1px solid #b9d2e8',
            'borderBottom': '1px solid #b9d2e8',
            'boxShadow':
                'inset 0 1px 0 rgba(255,255,255,.9), ' +
                'inset 0 -3px 4px rgba(16,48,82,.16), ' +
                'inset -2px 0 3px rgba(16,48,82,.08)'
        };
    }
    """
)

for col in [
    "quantity", "Quantity", "qty", "Qty",
    "rate", "Rate", "to_rate", "T.O Rate",
    "amount", "Amount"
]:

    if col in display_df.columns:

        gb.configure_column(col, cellStyle=numeric_cell_style_js)

decimal_value_formatter_js = JsCode(
    """
    function(params) {
        var v = params.value;
        if (v === null || v === undefined || v === '') { return ''; }
        var num = Number(v);
        if (isNaN(num)) { return v; }
        if (num === 0) { return '-'; }
        return num.toLocaleString('en-US', {
            minimumFractionDigits: 2, maximumFractionDigits: 2
        });
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
        return num.toLocaleString('en-US', {
            minimumFractionDigits: 0, maximumFractionDigits: 0
        });
    }
    """
)

for col in [
    "quantity", "Quantity", "qty", "Qty",
    "rate", "Rate", "to_rate", "T.O Rate"
]:

    if col in display_df.columns:

        gb.configure_column(col, valueFormatter=decimal_value_formatter_js)

for col in ["amount", "Amount"]:

    if col in display_df.columns:

        gb.configure_column(
            col, valueFormatter=amount_value_formatter_js, editable=False
        )

gb.configure_selection(
    selection_mode="multiple",
    use_checkbox=True,
    header_checkbox=True,
    suppressRowDeselection=False
)

gb.configure_side_bar(filters_panel=True, columns_panel=True)

gb.configure_grid_options(
    enableRangeSelection=True,
    enableFillHandle=True,
    rowHeight=34,
    headerHeight=40,
    suppressRowClickSelection=False,
    clipboardDelimiter="\t",
    getRowStyle=row_style_js,
    pagination=False,
    rowSelection="multiple",
    suppressRowDeselection=False,
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

grid_options = gb.build()

grid_custom_css = {
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
            "linear-gradient(180deg, #16324a 0%, #0a1b2e 100%) !important",
        "border-bottom": "3px solid #c9a227 !important"
    },
    ".ag-header-cell": {
        "border-right": "1px solid rgba(201,162,39,.35) !important",
        "box-shadow":
            "inset 0 1px 0 rgba(255,255,255,.10), "
            "inset 0 -2px 0 rgba(0,0,0,.30) !important"
    },
    ".ag-header-cell-label": {
        "font-family": "Georgia, 'Segoe UI', Cambria, serif !important",
        "font-weight": "700 !important",
        "justify-content": "center !important"
    },
    ".ag-header-cell-text": {
        "font-family": "Georgia, 'Segoe UI', Cambria, serif !important",
        "font-weight": "700 !important",
        "color": "#f4e4b8 !important",
        "font-size": "12.5px !important",
        "letter-spacing": "1.1px !important",
        "text-transform": "uppercase !important",
        "text-shadow": "0 1px 2px rgba(0,0,0,.55) !important"
    },
    ".ag-cell": {
        "border-color": "#d7e7f5 !important",
        "border-left": "1px solid rgba(255,255,255,.95) !important",
        "border-top": "1px solid rgba(255,255,255,.92) !important",
        "font-size": "13px !important",
        "line-height": "34px !important",
        "padding-left": "9px !important",
        "padding-right": "9px !important"
    },
    ".ag-cell-focus": {
        "box-shadow": "inset 0 0 0 2px #38d5ec !important"
    },
    ".ag-row-hover": {
        "background-color": "#dcf7ff !important"
    },
    ".ag-row-selected": {
        "background-color": "#caeff8 !important"
    },
    ".ag-floating-filter-input": {
        "border-radius": "5px !important",
        "border": "1px solid #b8c6d6 !important",
        "box-shadow": "inset 0 1px 3px rgba(16,32,51,.18) !important"
    },
    ".ag-side-bar": {
        "border-left": "1px solid #cbd6e2 !important"
    }
}

grid_response = AgGrid(
    display_df,
    gridOptions=grid_options,
    enable_enterprise_modules=False,
    height=700,
    fit_columns_on_grid_load=False,
    update_on=[
        "cellValueChanged", "selectionChanged",
        "filterChanged", "sortChanged"
    ],
    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    allow_unsafe_jscode=True,
    custom_css=grid_custom_css,
    key="main_grid"
)

edited_df = grid_response.get("data", display_df.copy())

if not isinstance(edited_df, pd.DataFrame):

    edited_df = pd.DataFrame(edited_df)

selected_rows = grid_response.get("selected_rows", [])

if selected_rows is None:

    selected_rows = pd.DataFrame()

elif isinstance(selected_rows, list):

    selected_rows = pd.DataFrame(selected_rows)

elif not isinstance(selected_rows, pd.DataFrame):

    selected_rows = pd.DataFrame(selected_rows)

if not selected_rows.empty:

    if "_row_type" in selected_rows.columns:

        selected_rows = selected_rows[
            selected_rows["_row_type"] == "data"
        ].copy()

    if "id" in selected_rows.columns:

        selected_rows = selected_rows[
            selected_rows["id"].notna()
        ].copy()


# ============================================================
# DELETE SECTION
# ============================================================

st.divider()

st.subheader("🗑️ Delete Selected Rows")

if selected_rows.empty or "id" not in selected_rows.columns:

    st.info(
        "☑️ Tick the checkbox on the left side of one or more data rows, "
        "then press Delete."
    )

else:

    selected_quantity = 0.0

    if qty_col and qty_col in selected_rows.columns:

        selected_quantity = pd.to_numeric(
            selected_rows[qty_col], errors="coerce"
        ).fillna(0).sum()

    selected_amount = 0.0

    if amount_col and amount_col in selected_rows.columns:

        selected_amount = pd.to_numeric(
            selected_rows[amount_col], errors="coerce"
        ).fillna(0).sum()

    st.warning(f"{len(selected_rows):,} row(s) selected.")

    d1, d2, d3 = st.columns(3)

    with d1:
        st.metric("Selected Records", f"{len(selected_rows):,}")

    with d2:
        st.metric("Selected Quantity", f"{selected_quantity:,.2f}")

    with d3:
        st.metric("Selected Amount", f"{selected_amount:,.2f}")

    preview_columns = [
        c for c in selected_rows.columns
        if c not in ("id", "_row_type")
    ]

    st.dataframe(
        selected_rows[preview_columns],
        use_container_width=True,
        hide_index=True
    )

    delete_clicked = st.button(
        f"🗑️ Delete {len(selected_rows):,} Selected Row(s)",
        type="primary"
    )

    if delete_clicked:

        conn = None
        cur = None

        try:

            ids_to_delete = []

            for value in selected_rows["id"].tolist():

                if pd.notna(value):

                    try:
                        ids_to_delete.append(int(value))
                    except (ValueError, TypeError):
                        pass

            ids_to_delete = list(dict.fromkeys(ids_to_delete))

            if ids_to_delete:

                conn = get_conn()
                cur = conn.cursor()

                cur.execute(
                    """
                    DELETE FROM supply_sheet
                    WHERE id = ANY(%s)
                    """,
                    (ids_to_delete,)
                )

                conn.commit()

                cur.close()
                cur = None

                conn.close()
                conn = None

                load_data.clear()
                get_table_columns.clear()

                st.success(
                    f"Deleted {len(ids_to_delete):,} row(s) successfully."
                )

                st.rerun()

            else:

                st.warning("No valid rows to delete.")

        except Exception as e:

            if conn is not None:
                try:
                    conn.rollback()
                except Exception:
                    pass

            if cur is not None:
                try:
                    cur.close()
                except Exception:
                    pass

            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

            st.error(f"❌ Failed to delete rows: {e}")


# ============================================================
# SAVE BUTTON
# ============================================================

st.divider()

save_clicked = st.button(
    "💾 Save Additions / Amendments to Database (Ctrl+S)",
    type="primary",
    use_container_width=False
)


# ============================================================
# SAVE
# ============================================================

if save_clicked:

    conn = None
    cur = None

    try:

        conn = get_conn()
        cur = conn.cursor()

        n_inserted = 0
        n_updated = 0

        # --------------------------------------------------------
        # 1. INSERT NEW ROWS
        # --------------------------------------------------------

        rows_to_insert = st.session_state.new_rows_df.dropna(how="all").copy()

        if len(rows_to_insert):

            insert_columns = [
                c for c in entry_columns
                if c not in generated_columns
                and c not in hidden_internal_columns
            ]

            cols_sql = ", ".join(f'"{c}"' for c in insert_columns)

            values = []

            for _, row in rows_to_insert.iterrows():

                row_values = []

                for c in insert_columns:

                    if c in numeric_entry_cols:

                        value = clean_numeric_value(row[c])

                    else:

                        try:

                            if pd.isna(row[c]):
                                value = None
                            else:
                                value = str(row[c]).strip()
                                if value == "":
                                    value = None

                        except Exception:

                            value = str(row[c]).strip()
                            if value == "":
                                value = None

                    row_values.append(value)

                values.append(tuple(row_values))

            if values:

                execute_values(
                    cur,
                    f"""
                    INSERT INTO supply_sheet
                    ({cols_sql})
                    VALUES %s
                    """,
                    values
                )

                n_inserted = len(values)

        # --------------------------------------------------------
        # 2. UPDATE EXISTING ROWS
        # --------------------------------------------------------

        if "id" in edited_df.columns and not edited_df.empty:

            original_by_id = {}

            for _, original_row in df.iterrows():

                original_id = original_row["id"]

                if pd.notna(original_id):

                    try:
                        original_by_id[int(original_id)] = original_row
                    except (ValueError, TypeError):
                        pass

            for _, row in edited_df.iterrows():

                if "_row_type" in edited_df.columns:

                    if row["_row_type"] != "data":
                        continue

                if pd.isna(row["id"]):
                    continue

                try:
                    rid = int(row["id"])
                except (ValueError, TypeError):
                    continue

                orig = original_by_id.get(rid)

                if orig is None:
                    continue

                changes = {}

                for c in entry_columns:

                    if c in generated_columns:
                        continue

                    if c not in edited_df.columns:
                        continue

                    is_num = c in numeric_entry_cols

                    new_norm = normalize_value(row[c], is_num)
                    old_norm = normalize_value(orig[c], is_num)

                    if new_norm != old_norm:

                        if is_num:
                            changes[c] = clean_numeric_value(row[c])
                        else:
                            changes[c] = new_norm

                if changes:

                    set_sql = ", ".join(
                        f'"{c}" = %s' for c in changes.keys()
                    )

                    sql = f"""
                        UPDATE supply_sheet
                        SET {set_sql}
                        WHERE id = %s
                    """

                    values_update = list(changes.values())
                    values_update.append(rid)

                    cur.execute(sql, values_update)

                    n_updated += 1

        # --------------------------------------------------------
        # COMMIT
        # --------------------------------------------------------

        conn.commit()

        cur.close()
        cur = None

        conn.close()
        conn = None

        st.session_state.new_rows_df = pd.DataFrame(columns=entry_columns)

        load_data.clear()
        get_table_columns.clear()

        st.success(
            f"Saved successfully — {n_inserted:,} added, "
            f"{n_updated:,} updated."
        )

        st.rerun()

    except Exception as e:

        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass

        if cur is not None:
            try:
                cur.close()
            except Exception:
                pass

        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

        st.error(f"❌ Failed to save changes: {e}")
