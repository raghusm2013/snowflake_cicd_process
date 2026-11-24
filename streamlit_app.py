import streamlit as st
from snowflake.snowpark.context import get_active_session

DB = "SNOWFLAKE_LEARNING_DB"

st.set_page_config(page_title="Information Schema Dashboard-Rerun test", layout="wide")
st.title("Information Schema Dashboard")
st.caption(f"Source: {DB}.INFORMATION_SCHEMA")

session = get_active_session()

@st.cache_data(ttl=600)
def run_query(sql: str, params: tuple = ()):
    return session.sql(sql, params=list(params) or None).to_pandas()

# 1. KPI counts
kpi = run_query(f"""
    SELECT
      (SELECT COUNT(*) FROM {DB}.INFORMATION_SCHEMA.SCHEMATA) AS SCHEMAS,
      (SELECT COUNT(*) FROM {DB}.INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE <> 'VIEW') AS TABLES,
      (SELECT COUNT(*) FROM {DB}.INFORMATION_SCHEMA.VIEWS) AS VIEWS,
      (SELECT COUNT(*) FROM {DB}.INFORMATION_SCHEMA.COLUMNS) AS COLUMNS
""")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Schemas", int(kpi["SCHEMAS"][0]))
c2.metric("Tables", int(kpi["TABLES"][0]))
c3.metric("Views", int(kpi["VIEWS"][0]))
c4.metric("Columns", int(kpi["COLUMNS"][0]))

# 2. Objects per schema
st.subheader("Objects per Schema")
per_schema = run_query(f"""
    SELECT TABLE_SCHEMA, TABLE_TYPE, COUNT(*) AS OBJECTS
    FROM {DB}.INFORMATION_SCHEMA.TABLES
    GROUP BY 1, 2 ORDER BY 1
""")
st.bar_chart(per_schema, x="TABLE_SCHEMA", y="OBJECTS", color="TABLE_TYPE")

# 3. View browser (fixed allowlist - no user-built SQL)
st.subheader("View Browser")
VIEWS = ["SCHEMATA", "TABLES", "VIEWS", "COLUMNS", "FUNCTIONS", "PROCEDURES", "STAGES"]
choice = st.selectbox("Select view", VIEWS)
df = run_query(f"SELECT * FROM {DB}.INFORMATION_SCHEMA.{choice} LIMIT 1000")
st.dataframe(df, use_container_width=True)

# 4 + 5. Column browser
st.subheader("Column Browser")
tables = run_query(f"""
    SELECT TABLE_SCHEMA || '.' || TABLE_NAME AS FQN, TABLE_SCHEMA, TABLE_NAME
    FROM {DB}.INFORMATION_SCHEMA.TABLES ORDER BY 1
""")
fqn = st.selectbox("Select table", tables["FQN"])
if fqn:
    row = tables[tables["FQN"] == fqn].iloc[0]
    cols = run_query(
        f"""SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, ORDINAL_POSITION
            FROM {DB}.INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION""",
        (row["TABLE_SCHEMA"], row["TABLE_NAME"]),
    )
    st.dataframe(cols, use_container_width=True)
