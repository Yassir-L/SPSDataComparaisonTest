import streamlit as st
import pandas as pd

# Constants
DEFAULT_FILE = "data/PRawMaterials_Datafile_PIEC_2024M11.xlsx"
P4_SHEETS_RAW_MATERIALS = [
    "P4__AssetList",
    "P4_Cap_O",
    "P4_Cap_H",
    "P4_UR",
    "P4_P",
    "P4_I",
    "P4_E",
    "P4_D"
]

# Header rows: specific per sheet
HEADER_ROWS = {
    "P4__AssetList": 6,
    "P4_Cap_O": 8,
    "P4_Cap_H": 8,
    "P4_UR": 8,
    "P4_P": 8,
    "P4_I": 8,
    "P4_E": 8,
    "P4_D": 8
}

def load_raw_materials_data(file_path):
    try:
        xl = pd.ExcelFile(file_path)
        data = {}
        for sheet in P4_SHEETS_RAW_MATERIALS:
            if sheet not in xl.sheet_names:
                data[sheet] = f"Sheet '{sheet}' not found"
                continue

            header_row = HEADER_ROWS.get(sheet, 0)
            df = xl.parse(sheet, header=header_row)
            data[sheet] = df

        return data
    except Exception as e:
        return {"error": str(e)}

def show():
    st.header("📄 Raw Materials Data Viewer")

    file_path = st.sidebar.text_input("Excel file name", value=DEFAULT_FILE)

    raw_data = load_raw_materials_data(file_path)

    for sheet_name, df in raw_data.items():
        with st.expander(f"📄 {sheet_name}"):
            if isinstance(df, str):
                st.warning(df)
            else:
                st.dataframe(df, use_container_width=True)
