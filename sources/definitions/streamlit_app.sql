DEFINE STREAMLIT
    {{database_name}}.{{schema_name}}.MY_STREAMLIT_APP
    FROM 'asset://metadata_explorer/'
    MAIN_FILE = 'streamlit_app.py'
    QUERY_WAREHOUSE = '{{warehouse_name}}'
    TITLE = 'Snowflake Metadata Explorer'
;
