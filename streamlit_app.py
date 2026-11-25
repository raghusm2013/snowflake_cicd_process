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
