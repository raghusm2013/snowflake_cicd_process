
import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

# --------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Snowflake Metadata Explored",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB = "SNOWFLAKE_LEARNING_DB"

# --------------------------------------------------
# 2. CUSTOM UI STYLING
# --------------------------------------------------

st.markdown("""
<style>
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2rem;
    }

    .dashboard-subtitle {
        color: #8492A6;
        font-size: 14px;
        margin-top: -12px;
        margin-bottom: 22px;
    }

    .section-heading {
        font-size: 19px;
        font-weight: 650;
        margin-bottom: 5px;
    }

    .section-caption {
        color: #8492A6;
        font-size: 13px;
        margin-bottom: 16px;
    }

    div[data-testid="stMetric"] {
        background-color: rgba(128, 128, 128, 0.08);
        border: 1px solid rgba(128, 128, 128, 0.18);
        padding: 18px;
        border-radius: 12px;
    }

    div[data-testid="stMetricLabel"] {
        font-size: 13px;
    }

    div[data-testid="stMetricValue"] {
        font-weight: 700;
    }

    .database-label {
        color: #8492A6;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# 3. SNOWFLAKE SESSION
# --------------------------------------------------

session = get_active_session()

@st.cache_data(ttl=600, show_spinner=False)
def run_query(sql: str, params: tuple = ()):
    return session.sql(
        sql,
        params=list(params) or None
    ).to_pandas()

# --------------------------------------------------
# 4. DASHBOARD HEADER
# --------------------------------------------------

header_left, header_right = st.columns([4, 1])

with header_left:
    st.title("❄️ Snowflake Metadata Explorer-Title")
    st.markdown(
        '<p class="dashboard-subtitle">'
        'Explore database objects, schemas, views and table structures.'
        '</p>',
        unsafe_allow_html=True
    )

with header_right:
    st.markdown(
        f'<div class="database-label">ACTIVE DATABASE</div>'
        f'<div style="font-size:17px;font-weight:650;">{DB}</div>',
        unsafe_allow_html=True
    )

st.divider()

# --------------------------------------------------
# 5. KPI METRICS
# --------------------------------------------------

with st.spinner("Loading database metadata..."):

    kpi = run_query(f"""
        SELECT
            (SELECT COUNT(*)
             FROM {DB}.INFORMATION_SCHEMA.SCHEMATA) AS SCHEMAS,

            (SELECT COUNT(*)
             FROM {DB}.INFORMATION_SCHEMA.TABLES
             WHERE TABLE_TYPE <> 'VIEW') AS TABLES,

            (SELECT COUNT(*)
             FROM {DB}.INFORMATION_SCHEMA.VIEWS) AS VIEWS,

            (SELECT COUNT(*)
             FROM {DB}.INFORMATION_SCHEMA.COLUMNS) AS COLUMNS
    """)

    schemas_count = int(kpi["SCHEMAS"].iloc[0])
    tables_count = int(kpi["TABLES"].iloc[0])
    views_count = int(kpi["VIEWS"].iloc[0])
    columns_count = int(kpi["COLUMNS"].iloc[0])

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric("📁 Schemas", f"{schemas_count:,}")

with m2:
    st.metric("🗂️ Tables", f"{tables_count:,}")

with m3:
    st.metric("📊 Views", f"{views_count:,}")

with m4:
    st.metric("🔢 Columns", f"{columns_count:,}")

st.write("")

# --------------------------------------------------
# 6. DASHBOARD TABS
# --------------------------------------------------

overview_tab, views_tab, columns_tab = st.tabs([
    "📈 Overview",
    "🔍 View Explorer",
    "🧱 Column Explorer"
])

# --------------------------------------------------
# TAB 1: OVERVIEW
# --------------------------------------------------

with overview_tab:

    st.markdown(
        '<div class="section-heading">Database Object Distribution</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-caption">'
        'Understand how database objects are distributed across schemas.'
        '</div>',
        unsafe_allow_html=True
    )

    per_schema = run_query(f"""
        SELECT
            TABLE_SCHEMA,
            TABLE_TYPE,
            COUNT(*) AS OBJECTS
        FROM {DB}.INFORMATION_SCHEMA.TABLES
        GROUP BY TABLE_SCHEMA, TABLE_TYPE
        ORDER BY TABLE_SCHEMA
    """)

    if not per_schema.empty:

        chart_col, summary_col = st.columns([3, 1])

        with chart_col:
            st.bar_chart(
                per_schema,
                x="TABLE_SCHEMA",
                y="OBJECTS",
                color="TABLE_TYPE",
                height=380
            )

        with summary_col:
            st.markdown("#### Object Summary")

            object_summary = (
                per_schema.groupby("TABLE_TYPE")["OBJECTS"]
                .sum()
                .reset_index()
            )

            for _, row in object_summary.iterrows():
                st.metric(
                    str(row["TABLE_TYPE"]).replace("_", " ").title(),
                    f"{int(row['OBJECTS']):,}"
                )

        with st.expander("View underlying metadata"):
            st.dataframe(
                per_schema,
                use_container_width=True,
                hide_index=True
            )

    else:
        st.info("No database objects found.")

# --------------------------------------------------
# TAB 2: VIEW EXPLORER
# --------------------------------------------------

with views_tab:

    st.markdown(
        '<div class="section-heading">Information Schema Browser</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-caption">'
        'Select an information schema view to explore its metadata.'
        '</div>',
        unsafe_allow_html=True
    )

    VIEWS = [
        "SCHEMATA",
        "TABLES",
        "VIEWS",
        "COLUMNS",
        "FUNCTIONS",
        "PROCEDURES",
        "STAGES"
    ]

    filter_col, info_col = st.columns([2, 3])

    with filter_col:
        choice = st.selectbox(
            "Select metadata view",
            VIEWS
        )

    with info_col:
        st.markdown("#### ")
        st.caption(
            f"Source: {DB}.INFORMATION_SCHEMA.{choice}"
        )

    df = run_query(f"""
        SELECT *
        FROM {DB}.INFORMATION_SCHEMA.{choice}
        LIMIT 1000
    """)

    st.write("")

    result_col, download_col = st.columns([4, 1])

    with result_col:
        st.markdown(f"**{len(df):,} records returned**")

    with download_col:
        st.download_button(
            label="⬇️ Download CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"{choice.lower()}_metadata.csv",
            mime="text/csv",
            use_container_width=True
        )

    search_text = st.text_input(
        "Filter displayed results",
        placeholder="Search metadata..."
    )

    if search_text:
        mask = df.astype(str).apply(
            lambda col: col.str.contains(
                search_text,
                case=False,
                na=False
            )
        ).any(axis=1)

        display_df = df[mask]
    else:
        display_df = df

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=430
    )

# --------------------------------------------------
# TAB 3: COLUMN EXPLORER
# --------------------------------------------------

with columns_tab:

    st.markdown(
        '<div class="section-heading">Table Structure Explorer</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-caption">'
        'Inspect table columns, data types and nullability.'
        '</div>',
        unsafe_allow_html=True
    )

    tables = run_query(f"""
        SELECT
            TABLE_SCHEMA,
            TABLE_NAME
        FROM {DB}.INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE <> 'VIEW'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """)

    if not tables.empty:

        schema_options = sorted(
            tables["TABLE_SCHEMA"].dropna().unique().tolist()
        )

        schema_col, table_col = st.columns(2)

        with schema_col:
            selected_schema = st.selectbox(
                "Select schema",
                schema_options
            )

        available_tables = tables[
            tables["TABLE_SCHEMA"] == selected_schema
        ]["TABLE_NAME"].tolist()

        with table_col:
            selected_table = st.selectbox(
                "Select table",
                available_tables
            )

        if selected_table:

            cols = run_query(
                f"""
                SELECT
                    COLUMN_NAME,
                    DATA_TYPE,
                    IS_NULLABLE,
                    ORDINAL_POSITION
                FROM {DB}.INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = ?
                  AND TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
                """,
                (selected_schema, selected_table)
            )

            st.divider()

            st.markdown(
                f"**{selected_schema}.{selected_table}**"
            )

            c1, c2 = st.columns(2)

            with c1:
                st.metric("Total Columns", len(cols))

            with c2:
                nullable_count = (
                    cols["IS_NULLABLE"] == "YES"
                ).sum()

                st.metric("Nullable Columns", int(nullable_count))

            st.dataframe(
                cols,
                use_container_width=True,
                hide_index=True,
                height=400
            )

    else:
        st.info("No tables found in this database.")

# --------------------------------------------------
# 7. FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "Snowflake Metadata Explorer | "
    "Powered by Streamlit and Snowflake Snowpark"
)
