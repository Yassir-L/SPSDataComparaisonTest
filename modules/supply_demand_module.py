###working like a charm V1
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from modules.rawdata import load_raw_p4_sheets
import os
import random

DEFAULT_FILE = "data/specialty-phosphates-market-outlook-database-february-2025-amended.xlsx"
METRICS = {
    "P4 Capacity": "Capacity",
    "P4 Production": "Production",
    "P4 Demand": "Demand",
    "P4 Exports": "Exports",
    "P4 Imports": "Imports"
}

@st.cache_data
def extract_level1_regions(df):
    return sorted(set(df.iloc[:, 0].astype(str).str.strip().dropna().unique()))

@st.cache_data
def extract_metric_row(df, region):
    df = df.copy()
    df = df.loc[:, ~df.columns.duplicated()]  # remove duplicate headers

    year_cols = [col for col in df.columns if str(col).isdigit()]
    df_years = df[["Unnamed: 0"] + year_cols] if "Unnamed: 0" in df.columns else df[[df.columns[0]] + year_cols]
    df_years.columns = ["Region"] + year_cols

    match = df_years[df_years["Region"].astype(str).str.strip() == region]
    if not match.empty:
        row = match.iloc[0][year_cols]
        row = row[~row.index.duplicated(keep="first")]
        row.index = pd.Series(row.index).astype(int)
        return pd.to_numeric(row, errors="coerce")
    return pd.Series([None] * len(year_cols), index=pd.Series(year_cols).astype(int))

def show():
    st.header("📊 P4 Supply & Demand Table")

    file_path = st.text_input("Excel file name", value=DEFAULT_FILE)
    raw_data = load_raw_p4_sheets(file_path)

    # Reference for dropdown values
    base_sheet = raw_data.get("P4 Capacity")
    if not isinstance(base_sheet, pd.DataFrame):
        st.error("Failed to load 'P4 Capacity'.")
        return

    region_options = extract_level1_regions(base_sheet)
    region = st.selectbox("🌍 Select major region", ["World Total"] + region_options, index=0)

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

    st.dataframe(
        summary_df.style.format(lambda x: f"{x:,.0f}" if pd.notnull(x) else ""),
        use_container_width=True
    )

    # ------------- 📈 Charts --------------
    years = summary_df.columns.astype(int)

    # Supply Chart: Overlapping Bars (not stacked)
    fig_supply = go.Figure()
    fig_supply.add_trace(go.Bar(
        x=years, y=summary_df.loc["Capacity"],
        name="Capacity", marker_color="lightsteelblue", opacity=1
    ))
    fig_supply.add_trace(go.Bar(
        x=years, y=summary_df.loc["Production"],
        name="Production", marker_color="steelblue", opacity=0.9
    ))
    fig_supply.add_trace(go.Scatter(
        x=years, y=summary_df.loc["Exports"],
        name="Exports", mode="lines+markers",
        line=dict(color="white"),
        marker=dict(color="black", size=6, line=dict(width=2, color="white"))
    ))
    fig_supply.update_layout(
        barmode="overlay",  # <-- overlap, not stack
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
        font_color="white", height=400,
        margin=dict(t=20, b=40, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # Demand Chart (still fine as stacked)
    fig_demand = go.Figure()
    fig_demand.add_trace(go.Bar(
        x=years, y=summary_df.loc["Demand"],
        name="Demand", marker_color="mediumturquoise"
    ))
    fig_demand.add_trace(go.Scatter(
        x=years, y=summary_df.loc["Imports"],
        name="Imports", mode="lines+markers",
        line=dict(color="white"),
        marker=dict(color="black", size=6, line=dict(width=2, color="white"))
    ))
    fig_demand.update_layout(
        barmode="stack",
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
        font_color="white", height=400,
        margin=dict(t=20, b=40, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # Display side by side with titles outside
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"##### 📈 {region} Supply, '000 t/y P4")
        st.plotly_chart(fig_supply, use_container_width=True)

    with col2:
        st.markdown(f"##### 📈 {region} Demand, '000 t/y P4")
        st.plotly_chart(fig_demand, use_container_width=True)
    
    
    
    import plotly.express as px
    from geopy.geocoders import Nominatim
    from geopy.extra.rate_limiter import RateLimiter
    
   

    # ------------------------------
    # 📊 Pareto Chart by Country + Company
    # ------------------------------
    st.subheader("📊 Pareto Chart: Capacity by Country")
    
    df_caplist = raw_data.get("P4 Capacity list")
    if not isinstance(df_caplist, pd.DataFrame):
        st.warning("⚠️ 'P4 Capacity list' not available.")
        return
    
    # Clean headers and select year
    df_caplist.columns = df_caplist.columns.map(str)
    year_col = str(st.slider("📅 Select Year for Pareto", 2010, 2029, 2021))
    
    if year_col not in df_caplist.columns:
        st.warning(f"Year {year_col} not found in dataset.")
        return
    
    # Process country-level data
    df_pareto = df_caplist[["Country", "Company", year_col]].copy()
    df_pareto = df_pareto.rename(columns={year_col: "Capacity"})
    df_pareto["Capacity"] = pd.to_numeric(df_pareto["Capacity"], errors="coerce")
    df_pareto = df_pareto.dropna(subset=["Country", "Capacity"])
    df_country = df_pareto.groupby("Country", as_index=False)["Capacity"].sum()
    df_country = df_country.sort_values("Capacity", ascending=False)
    df_country["Cumulative"] = df_country["Capacity"].cumsum()
    df_country["Cumulative %"] = df_country["Cumulative"] / df_country["Capacity"].sum() * 100
    
    # Country Pareto Chart with values
    fig_country = go.Figure()
    fig_country.add_trace(go.Bar(
        x=df_country["Country"],
        y=df_country["Capacity"],
        text=df_country["Capacity"].round(0).astype(int),
        textposition="auto",
        name="Capacity",
        marker_color="steelblue"
    ))
    fig_country.add_trace(go.Scatter(
        x=df_country["Country"],
        y=df_country["Cumulative %"],
        name="Cumulative %",
        yaxis="y2",
        mode="lines+markers",
        line=dict(color="crimson")
    ))
    fig_country.update_layout(
        yaxis=dict(title="Capacity"),
        yaxis2=dict(title="Cumulative %", overlaying="y", side="right", showgrid=False),
        xaxis=dict(title="Country"),
        height=450,
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font_color="white",
        margin=dict(t=40, b=40, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_country, use_container_width=True)
    
    # Company-level Drilldown
    #selected_country = st.selectbox("🔍 Select Country to Explore Companies", df_country["Country"])
    #top_n = st.selectbox("🏭 Companies to Show", options=["All", 3, 5, 7, 10,20,30], index=0, key="n_companies_dropdown")
    
    col_country, col_limit = st.columns([3, 2])
    with col_country:
        selected_country = st.selectbox("🔍 Select Country to Explore Companies", df_country["Country"])
    with col_limit:
        top_n = st.selectbox("🏭 Companies to Show", options=["All", 3, 7, 10, 20, 30, 35, 40], index=7, key="n_companies_dropdown")
    
    df_company = df_pareto[df_pareto["Country"] == selected_country]
    df_company = df_company.groupby("Company", as_index=False)["Capacity"].sum()
    df_company = df_company.sort_values("Capacity", ascending=False)
    
    if top_n != "All":
        df_company = df_company.head(int(top_n))
    
    df_company["Cumulative"] = df_company["Capacity"].cumsum()
    df_company["Cumulative %"] = df_company["Cumulative"] / df_company["Capacity"].sum() * 100
    

    
    fig_company = go.Figure()
    fig_company.add_trace(go.Bar(
        x=df_company["Company"],
        y=df_company["Capacity"],
        #text=df_company["Capacity"].round(0).astype(int),
        textposition="auto",
        name="Capacity",
        marker_color="mediumseagreen"
    ))
    fig_company.add_trace(go.Scatter(
        x=df_company["Company"],
        y=df_company["Cumulative %"],
        name="Cumulative %",
        yaxis="y2",
        mode="lines+markers",
        line=dict(color="darkgreen")
    ))
    fig_company.update_layout(
        yaxis=dict(title="Capacity"),
        yaxis2=dict(title="Cumulative %", overlaying="y", side="right", showgrid=False),
        xaxis=dict(title="Company"),
        height=450,
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font_color="white",
        margin=dict(t=40, b=40, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.subheader(f"🏭 Capacity Breakdown in {selected_country}")

    st.plotly_chart(fig_company, use_container_width=True)
   # ------------------------------
    # 📈 Capacity Evolution Over Time by Country (with World Total)
    # ------------------------------
    st.subheader("📈 Capacity Evolution Over Time by Country")
    
    df_caplist = raw_data.get("P4 Capacity list")
    if isinstance(df_caplist, pd.DataFrame):
        df_caplist.columns = df_caplist.columns.map(str)
    
        year_cols = [col for col in df_caplist.columns if col.isdigit()]
        meta_cols = ["Country"]
    
        # ---- Extract World Total ----
        world_row = df_caplist[df_caplist["Country"].isna() | (df_caplist["Country"].astype(str).str.strip() == "")]
        df_world = world_row[year_cols].copy()
        df_world["Country"] = "World Total"
        df_world = df_world.melt(id_vars="Country", var_name="Year", value_name="Capacity")
    
        # ---- Extract All Other Countries ----
        df_long = df_caplist[meta_cols + year_cols].dropna(subset=["Country"]).copy()
        df_long = df_long.melt(id_vars="Country", var_name="Year", value_name="Capacity")
    
        # Combine World and others
        combined = pd.concat([df_long, df_world], ignore_index=True)
        combined["Capacity"] = pd.to_numeric(combined["Capacity"], errors="coerce")
        combined = combined.dropna(subset=["Capacity"])
        combined["Year"] = combined["Year"].astype(int)
    
        # Grouped sum (per Country & Year)
        df_grouped = combined.groupby(["Country", "Year"], as_index=False)["Capacity"].sum()
    
        # Setup color and line settings
        df_grouped["color"] = df_grouped["Country"].apply(
            lambda x: "crimson" if x.strip().lower() == "world total" else "lightgray"
        )
        df_grouped["line_name"] = df_grouped["Country"].apply(
            lambda x: "🌍 World Total" if x.strip().lower() == "world total" else x
        )
    
        # Plotting
        fig_lines = go.Figure()
        for country in df_grouped["Country"].unique():
            df_c = df_grouped[df_grouped["Country"] == country]
            fig_lines.add_trace(go.Scatter(
                x=df_c["Year"],
                y=df_c["Capacity"],
                mode="lines+markers",
                name=df_c["line_name"].iloc[0],
                line=dict(
                    width=3 if country.lower().strip() == "world total" else 1.5,
                    color="crimson" if country.lower().strip() == "world total" else None
                ),
                opacity=1.0 if country.lower().strip() == "world total" else 0.5
            ))
    
        fig_lines.update_layout(
            height=500,
            xaxis_title="Year",
            yaxis_title="Capacity (kt/y)",
            plot_bgcolor="#0e1117",
            paper_bgcolor="#0e1117",
            font_color="white",
            legend_title="Country",
            margin=dict(t=30, b=40, l=20, r=20)
        )
    
        st.plotly_chart(fig_lines, use_container_width=True)
    else:
        st.warning("Could not load 'P4 Capacity list' for country evolution.")

        