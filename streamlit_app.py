
import streamlit as st
from snowflake.snowpark.context import get_active_session

st.title("Customer Dashboard")

session = get_active_session()

df = session.sql("""
    SELECT *
    FROM DEMO_DB.PUBLIC.CUSTOMERS
    LIMIT 100
""").to_pandas()

st.subheader("Customer Details")
st.dataframe(df, use_container_width=True)
