import streamlit as st
import pandas as pd
import re
from datetime import datetime, date
from db import get_engine


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI ERP Assistant",
    page_icon="🤖",
    layout="wide"
)


# ============================================================
# DATABASE
# ============================================================

@st.cache_resource
def get_db_engine():
    return get_engine()


try:
    engine = get_db_engine()
    db_connected = True
except Exception as e:
    engine = None
    db_connected = False


# ============================================================
# HEADER
# ============================================================

st.title("🤖 AI ERP Assistant")
st.caption(
    "Ask about branches, dates, invoices, quantities, "
    "amounts and totals in normal language."
)


if not db_connected:

    st.error(
        "Database connection failed. "
        "Please check your .streamlit/secrets.toml."
    )

    st.stop()


# ============================================================
# DATABASE INFORMATION
# ============================================================

@st.cache_data(ttl=300)
def get_database_schema():

    query = """
        SELECT
            table_name,
            column_name,
            data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
    """

    return pd.read_sql(query, engine)


@st.cache_data(ttl=300)
def get_branches():

    query = """
        SELECT DISTINCT TRIM(branch) AS branch
        FROM supply_sheet
        WHERE branch IS NOT NULL
          AND TRIM(branch) <> ''
        ORDER BY TRIM(branch)
    """

    return pd.read_sql(query, engine)


schema_df = get_database_schema()

try:
    branches_df = get_branches()
    branch_list = branches_df["branch"].dropna().tolist()
except Exception:
    branch_list = []


# ============================================================
# BRANCH DETECTION
# ============================================================

def detect_branch(question):

    q = question.lower()

    # Longest names first
    # This prevents a short branch name matching part
    # of a longer branch name.

    sorted_branches = sorted(
        branch_list,
        key=lambda x: len(str(x)),
        reverse=True
    )

    for branch in sorted_branches:

        branch_text = str(branch).strip()

        if branch_text.lower() in q:
            return branch_text

    return None


# ============================================================
# DATE DETECTION
# ============================================================

def detect_date(question):

    q = question.lower()

    months = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12
    }

    # Example:
    # 3 July
    # 3rd July
    # 03 July 2026

    pattern = (
        r"\b(\d{1,2})"
        r"(?:st|nd|rd|th)?\s+"
        r"(january|february|march|april|may|june|july|"
        r"august|september|october|november|december)"
        r"(?:\s+(\d{4}))?\b"
    )

    match = re.search(pattern, q)

    if match:

        day = int(match.group(1))
        month = months[match.group(2)]

        if match.group(3):
            year = int(match.group(3))
        else:
            year = 2026

        try:
            return datetime(
                year,
                month,
                day
            ).date()

        except ValueError:
            return None

    # ISO date
    # 2026-07-03

    iso_match = re.search(
        r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b",
        q
    )

    if iso_match:

        try:

            return date(
                int(iso_match.group(1)),
                int(iso_match.group(2)),
                int(iso_match.group(3))
            )

        except ValueError:
            return None

    return None


# ============================================================
# DATE RANGE DETECTION
# ============================================================

def detect_date_range(question):

    q = question.lower()

    months = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12
    }

    pattern = (
        r"(\d{1,2})(?:st|nd|rd|th)?\s+"
        r"(january|february|march|april|may|june|july|"
        r"august|september|october|november|december)"
        r"(?:\s+(\d{4}))?"
        r"\s*(?:to|-)\s*"
        r"(\d{1,2})(?:st|nd|rd|th)?\s+"
        r"(january|february|march|april|may|june|july|"
        r"august|september|october|november|december)"
        r"(?:\s+(\d{4}))?"
    )

    match = re.search(pattern, q)

    if not match:
        return None, None

    day1 = int(match.group(1))
    month1 = months[match.group(2)]

    year1 = (
        int(match.group(3))
        if match.group(3)
        else 2026
    )

    day2 = int(match.group(4))
    month2 = months[match.group(5)]

    year2 = (
        int(match.group(6))
        if match.group(6)
        else year1
    )

    try:

        return (
            date(year1, month1, day1),
            date(year2, month2, day2)
        )

    except ValueError:

        return None, None


# ============================================================
# QUESTION TYPE
# ============================================================

def detect_question_type(question):

    q = question.lower()

    if any(
        word in q
        for word in [
            "compare",
            "comparison",
            "highest",
            "lowest",
            "more than",
            "less than",
            "difference",
            "versus",
            "vs"
        ]
    ):
        return "comparison"

    if any(
        word in q
        for word in [
            "invoice",
            "invoices",
            "inv no",
            "inv #",
            "bill",
            "bills"
        ]
    ):
        return "invoice"

    if any(
        word in q
        for word in [
            "quantity",
            "qty",
            "units"
        ]
    ):
        return "quantity"

    if any(
        word in q
        for word in [
            "amount",
            "sale",
            "sales",
            "purchase",
            "purchases",
            "revenue",
            "total",
            "value"
        ]
    ):
        return "amount"

    return "data"


# ============================================================
# GET SUPPLY DATA
# ============================================================

def get_supply_data(
    branch=None,
    inv_date=None,
    start_date=None,
    end_date=None
):

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
        WHERE 1 = 1
    """

    params = {}

    if branch:

        query += """
            AND UPPER(TRIM(branch)) =
                UPPER(TRIM(%(branch)s))
        """

        params["branch"] = branch

    if inv_date:

        query += """
            AND inv_date = %(inv_date)s
        """

        params["inv_date"] = inv_date

    if start_date and end_date:

        query += """
            AND inv_date BETWEEN
                %(start_date)s AND %(end_date)s
        """

        params["start_date"] = start_date
        params["end_date"] = end_date

    query += """
        ORDER BY inv_date, inv_no, id
    """

    return pd.read_sql(
        query,
        engine,
        params=params
    )


# ============================================================
# SUMMARIZE DATA
# ============================================================

def summarize_data(df):

    if df.empty:

        return {
            "records": 0,
            "quantity": 0,
            "amount": 0
        }

    quantity = (
        pd.to_numeric(
            df["quantity"],
            errors="coerce"
        )
        .fillna(0)
        .sum()
    )

    amount = (
        pd.to_numeric(
            df["amount"],
            errors="coerce"
        )
        .fillna(0)
        .sum()
    )

    return {
        "records": len(df),
        "quantity": quantity,
        "amount": amount
    }


# ============================================================
# DISPLAY RESULT
# ============================================================

def display_result(df, question_type):

    if df.empty:

        st.warning(
            "No records found for the requested criteria."
        )

        return (
            "I couldn't find any records matching "
            "your request."
        )

    summary = summarize_data(df)

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Records",
            f"{summary['records']:,}"
        )

    with col2:

        st.metric(
            "Total Quantity",
            f"{summary['quantity']:,.2f}"
        )

    with col3:

        st.metric(
            "Total Amount",
            f"Rs. {summary['amount']:,.2f}"
        )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    if question_type == "quantity":

        response = (
            f"Total quantity is "
            f"**{summary['quantity']:,.2f}** "
            f"across {summary['records']:,} records."
        )

    elif question_type == "invoice":

        invoice_count = df["inv_no"].nunique()

        response = (
            f"I found **{invoice_count:,} invoices** "
            f"covering {summary['records']:,} records."
        )

    else:

        response = (
            f"I found **{summary['records']:,} records** "
            f"with a total amount of "
            f"**Rs. {summary['amount']:,.2f}**."
        )

    st.markdown(response)

    return response


# ============================================================
# CHAT HISTORY
# ============================================================

if "chat_messages" not in st.session_state:

    st.session_state.chat_messages = []


for message in st.session_state.chat_messages:

    with st.chat_message(message["role"]):

        if isinstance(
            message["content"],
            pd.DataFrame
        ):

            st.dataframe(
                message["content"],
                use_container_width=True,
                hide_index=True
            )

        else:

            st.markdown(
                message["content"]
            )


# ============================================================
# CHAT INPUT
# ============================================================

question = st.chat_input(
    "Example: Show Bahadurabad sales for 3 July 2026"
)


# ============================================================
# PROCESS QUESTION
# ============================================================

if question:

    st.session_state.chat_messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    with st.chat_message("user"):

        st.markdown(question)


    with st.chat_message("assistant"):

        # ----------------------------------------------------
        # Understand question
        # ----------------------------------------------------

        branch = detect_branch(question)

        single_date = detect_date(question)

        start_date, end_date = detect_date_range(question)

        question_type = detect_question_type(question)


        # ----------------------------------------------------
        # Display understanding
        # ----------------------------------------------------

        detected = []

        if branch:

            detected.append(
                f"**Branch:** {branch}"
            )

        if start_date and end_date:

            detected.append(
                f"**Date Range:** "
                f"{start_date.strftime('%d %b %Y')} "
                f"to "
                f"{end_date.strftime('%d %b %Y')}"
            )

        elif single_date:

            detected.append(
                f"**Date:** "
                f"{single_date.strftime('%d %B %Y')}"
            )

        if question_type:

            detected.append(
                f"**Query:** {question_type.title()}"
            )

        if detected:

            st.caption(
                " | ".join(detected)
            )


        # ----------------------------------------------------
        # Query database
        # ----------------------------------------------------

        try:

            # Date range has priority

            if start_date and end_date:

                df = get_supply_data(
                    branch=branch,
                    start_date=start_date,
                    end_date=end_date
                )

            else:

                df = get_supply_data(
                    branch=branch,
                    inv_date=single_date
                )


            # ------------------------------------------------
            # Result
            # ------------------------------------------------

            response = display_result(
                df,
                question_type
            )


            # ------------------------------------------------
            # Save response
            # ------------------------------------------------

            st.session_state.chat_messages.append(
                {
                    "role": "assistant",
                    "content": response
                }
            )


            if not df.empty:

                st.session_state.chat_messages.append(
                    {
                        "role": "assistant",
                        "content": df
                    }
                )


        except Exception as e:

            error_message = (
                f"❌ Database query failed:\n\n"
                f"`{e}`"
            )

            st.error(error_message)

            st.session_state.chat_messages.append(
                {
                    "role": "assistant",
                    "content": error_message
                }
            )


# ============================================================
# SIDEBAR INFORMATION
# ============================================================

with st.sidebar:

    st.header("🤖 AI ERP Assistant")

    st.write(
        "Ask questions about your ERP data."
    )

    st.divider()

    st.subheader("Examples")

    st.write(
        "• I want BTK 3rd July data"
    )

    st.write(
        "• Show Bahadurabad data"
    )

    st.write(
        "• Bahadurabad sales on 3 July"
    )

    st.write(
        "• Show BTK invoices for July"
    )

    st.write(
        "• Total quantity for Karachi"
    )

    st.write(
        "• Total amount for BTK on 3 July"
    )

    st.write(
        "• Show BTK data from 1 July to 10 July"
    )

    st.divider()

    st.caption(
        f"Branches found in database: "
        f"{len(branch_list)}"
    )