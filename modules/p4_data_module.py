# modules/p4_data_module.py

import streamlit as st
from modules.rawdata import load_raw_p4_sheets

DEFAULT_FILE = "data/specialty-phosphates-market-outlook-database-february-2025-amended.xlsx"

def show():
    st.header("📄 P4 Raw Data Viewer")

    file_path = st.sidebar.text_input("Excel file name", value=DEFAULT_FILE)

    raw_data = load_raw_p4_sheets(file_path)

    for sheet_name, df in raw_data.items():
        with st.expander(f"📄 {sheet_name}"):
            if isinstance(df, str):
                st.warning(df)
            else:
                st.dataframe(df, use_container_width=True)
