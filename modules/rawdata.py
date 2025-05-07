import pandas as pd

P4_SHEETS = [
    "P4 Capacity list",
    "P4 Capacity",
    "P4 Production",
    "P4 Demand",
    "P4 Imports",
    "P4 Exports",
    "P4 2021 Trade",
    "P4 2022 Trade",
    "P4 2023  Trade"
]

def load_raw_p4_sheets(file_path):
    try:
        xl = pd.ExcelFile(file_path)
        data = {}
        for sheet in P4_SHEETS:
            if sheet not in xl.sheet_names:
                data[sheet] = f"Sheet '{sheet}' not found"
                continue

            # Only "P4 Capacity List" uses row 4 (index 3) as header
            if sheet == "P4 Capacity list":
                df = xl.parse(sheet, header=3)
            else:
                df = xl.parse(sheet, header=2)

            data[sheet] = df

        return data
    except Exception as e:
        return {"error": str(e)}
