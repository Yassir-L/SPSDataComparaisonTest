import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from modules.raw_materials_data_module import load_raw_materials_data

DEFAULT_FILE = "data/PRawMaterials_Datafile_PIEC_2024M11.xlsx"

METRICS = {
    "P4_Cap_O": "Capacity",
    "P4_P": "Production",
    "P4_D": "Demand",
    "P4_E": "Exports",
    "P4_I": "Imports"
}

def extract_metric_row(df, region):
    df = df.copy()
    df.columns = df.columns.map(str)
    year_cols = [col for col in df.columns if col.isdigit() and 2010 <= int(col) <= 2050]

    region_col = [col for col in df.columns if "Geography" in col or "Region" in col][0]
    match = df[df[region_col].astype(str).str.strip().str.lower() == region.lower()]

    if not match.empty:
        row = match.iloc[0][year_cols]
        row.index = pd.Series(row.index).astype(int)
        return pd.to_numeric(row, errors="coerce")
    return pd.Series([None] * len(year_cols), index=pd.Series(year_cols).astype(int))

def show():
    st.header("📊 Raw Materials – P4 S&P Global Analysis")

    file_path = st.text_input("Excel file name", value=DEFAULT_FILE)
    raw_data = load_raw_materials_data(file_path)

    region = st.selectbox("🌍 Select region for summary (from Geography column)", ["Global", "China (mainland)", "United States", "Europe"])
    end_year = st.slider("📅 Select last year to show", 2020, 2050, 2030)

    summary_data = {}
    for sheet, metric in METRICS.items():
        df = raw_data.get(sheet)
        if isinstance(df, pd.DataFrame):
            row = extract_metric_row(df, region)
            summary_data[metric] = row

    summary_df = pd.DataFrame.from_dict(summary_data, orient="index")
    summary_df.index.name = "Metric"
    summary_df.columns.name = "Year"
    summary_df = summary_df.sort_index(axis=1)

    st.dataframe(summary_df.style.format(lambda x: f"{x:,.0f}" if pd.notnull(x) else ""), use_container_width=True)

    # Charts
    years = summary_df.columns.astype(int)
    years = years[years <= end_year]

    fig_supply = go.Figure()
    fig_supply.add_trace(go.Bar(x=years, y=summary_df.loc["Capacity", years], name="Capacity", marker_color="lightsteelblue"))
    fig_supply.add_trace(go.Bar(x=years, y=summary_df.loc["Production", years], name="Production", marker_color="steelblue"))
    fig_supply.add_trace(go.Scatter(x=years, y=summary_df.loc["Exports", years], name="Exports", mode="lines+markers", line=dict(color="white"), marker=dict(color="black", size=6, line=dict(width=2, color="white"))))
    fig_supply.update_layout(barmode="overlay", plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font_color="white", height=400)

    fig_demand = go.Figure()
    fig_demand.add_trace(go.Bar(x=years, y=summary_df.loc["Demand", years], name="Demand", marker_color="mediumturquoise"))
    fig_demand.add_trace(go.Scatter(x=years, y=summary_df.loc["Imports", years], name="Imports", mode="lines+markers", line=dict(color="white"), marker=dict(color="black", size=6, line=dict(width=2, color="white"))))
    fig_demand.update_layout(barmode="stack", plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font_color="white", height=400)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"##### 📈 {region} Supply, kt/y P4")
        st.plotly_chart(fig_supply, use_container_width=True)
    with col2:
        st.markdown(f"##### 📈 {region} Demand, kt/y P4")
        st.plotly_chart(fig_demand, use_container_width=True)

    # Pareto Chart by Country (P4_Cap_O)
    st.subheader("📊 Pareto Chart: Capacity by Country")
    df_cap = raw_data.get("P4_Cap_O")
    if isinstance(df_cap, pd.DataFrame):
        df_cap.columns = df_cap.columns.map(str)
        year_col = str(end_year)

        top_n = st.selectbox("🔢 Number of countries to display", options=[5, 10, 15, 20, "All"], index=1)

        df_pareto = df_cap[["Geography", year_col]].copy()
        df_pareto = df_pareto.rename(columns={"Geography": "Country", year_col: "Capacity"})
        df_pareto["Capacity"] = pd.to_numeric(df_pareto["Capacity"], errors="coerce")
        df_pareto = df_pareto.dropna(subset=["Country", "Capacity"])

        # Extract Global for KPI display
        global_row = df_pareto[df_pareto["Country"].str.strip().str.lower() == "global"]
        global_capacity = global_row["Capacity"].sum() if not global_row.empty else 0
        st.markdown(f"### 🌐 Global Capacity in {end_year}: **{global_capacity:,.0f} kt/y**")

        df_pareto = df_pareto[df_pareto["Country"].str.strip().str.lower() != "global"]

        df_country = df_pareto.groupby("Country", as_index=False)["Capacity"].sum()
        df_country = df_country.sort_values("Capacity", ascending=False)

        if top_n != "All":
            df_country = df_country.head(int(top_n))

        df_country["Cumulative"] = df_country["Capacity"].cumsum()
        df_country["Cumulative %"] = df_country["Cumulative"] / df_country["Capacity"].sum() * 100

        fig_country = go.Figure()
        fig_country.add_trace(go.Bar(x=df_country["Country"], y=df_country["Capacity"], text=df_country["Capacity"].round(0).astype(int), textposition="auto", name="Capacity", marker_color="steelblue"))
        fig_country.add_trace(go.Scatter(x=df_country["Country"], y=df_country["Cumulative %"], name="Cumulative %", yaxis="y2", mode="lines+markers", line=dict(color="crimson")))
        fig_country.update_layout(yaxis=dict(title="Capacity"), yaxis2=dict(title="Cumulative %", overlaying="y", side="right", showgrid=False), xaxis=dict(title="Country"), height=450, plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font_color="white")
        st.plotly_chart(fig_country, use_container_width=True)

    # Capacity Evolution Over Time by Region (Filtered Geography column + Global)
    st.subheader("📈 Capacity Evolution Over Time by Region (including Global)")
    
    if isinstance(df_cap, pd.DataFrame):
        df_cap.columns = df_cap.columns.map(str)
        year_cols = [col for col in df_cap.columns if col.isdigit() and 2010 <= int(col) <= end_year]
    
        valid_regions = [
            "Europe", "Eurasia", "Africa", "Middle East",
            "Asia", "Oceania", "Americas", "Antarctica", "Undefined", "Global"
        ]
    
        if "Geography" in df_cap.columns:
            df_filtered = df_cap[df_cap["Geography"].isin(valid_regions)]
        else:
            st.warning("Column 'Geography' not found in P4_Cap_O.")
            df_filtered = pd.DataFrame()
    
        if not df_filtered.empty:
            df_long = df_filtered[["Geography"] + year_cols].copy()
            df_long = df_long.melt(id_vars="Geography", var_name="Year", value_name="Capacity")
            df_long["Capacity"] = pd.to_numeric(df_long["Capacity"], errors="coerce")
            df_long = df_long.dropna(subset=["Capacity"])
            df_long["Year"] = df_long["Year"].astype(int)
    
            df_grouped = df_long.groupby(["Geography", "Year"], as_index=False)["Capacity"].sum()
    
            fig_lines = go.Figure()
            for region in valid_regions:
                df_r = df_grouped[df_grouped["Geography"] == region]
                if not df_r.empty:
                    fig_lines.add_trace(go.Scatter(
                        x=df_r["Year"],
                        y=df_r["Capacity"],
                        mode="lines+markers",
                        name=region,
                        line=dict(width=3 if region == "Global" else 1.5, color="crimson" if region == "Global" else None),
                        opacity=1.0 if region == "Global" else 0.6
                    ))
    
            fig_lines.update_layout(
                height=500,
                xaxis_title="Year",
                yaxis_title="Capacity (kt/y)",
                plot_bgcolor="#0e1117",
                paper_bgcolor="#0e1117",
                font_color="white",
                legend_title="Region"
            )
    
            st.plotly_chart(fig_lines, use_container_width=True)
        else:
            st.warning("No matching regions found in the 'Geography' column.")

