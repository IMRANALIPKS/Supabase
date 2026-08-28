import streamlit as st
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.engine import URL


url = URL.create(
    drivername="postgresql+psycopg2",
    username=st.secrets["DB_USER"],
    password=st.secrets["DB_PASSWORD"],
    host=st.secrets["DB_HOST"],
    port=int(st.secrets["DB_PORT"]),
    database=st.secrets["DB_NAME"],
)


@st.cache_resource
def get_engine():
    return create_engine(
        url,
        pool_pre_ping=True
    )


def get_conn():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"],
        port=int(st.secrets["DB_PORT"]),
        dbname=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
    )