import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from modules.raw_materials_data_module import load_raw_materials_data
from modules.rawdata import load_raw_p4_sheets

CRU_FILE = "data/specialty-phosphates-market-outlook-database-february-2025-amended.xlsx"
SPG_FILE = "data/PRawMaterials_Datafile_PIEC_2024M11.xlsx"

CRU_SHEET = "P4 Capacity list"
SPG_SHEET = "P4__AssetList"

COUNTRY_NAME_FIXES = {
    "China (mainland)": "China",
    "U.S.A.": "United States",
    "USA": "United States",
    "Korea, Republic of": "South Korea"
}

def standardize_country_name(name):
    if isinstance(name, str):
        name = name.strip()
        return COUNTRY_NAME_FIXES.get(name, name)
    return name

def extract_cru_table(df, year):
    df.columns = df.columns.map(str)
    if "Country" not in df.columns or str(year) not in df.columns:
        return pd.DataFrame(columns=["Country", "Capacity"])
    df = df[["Country", str(year)]].copy()
    df["Country"] = df["Country"].apply(standardize_country_name)
    df[str(year)] = pd.to_numeric(df[str(year)], errors="coerce")
    df = df.dropna()
    df = df.rename(columns={str(year): "Capacity"})
    df = df.groupby("Country", as_index=False).sum()
    return df

def extract_spg_table(df, year):
    df.columns = df.columns.map(str)
    if "Geography" not in df.columns or str(year) not in df.columns:
        return pd.DataFrame(columns=["Country", "Capacity"])
    df = df[["Geography", str(year)]].copy()
    df = df.rename(columns={"Geography": "Country", str(year): "Capacity"})
    df["Country"] = df["Country"].apply(standardize_country_name)
    df["Capacity"] = pd.to_numeric(df["Capacity"], errors="coerce")
    df = df.dropna()
    df = df.groupby("Country", as_index=False).sum()
    return df

def show():
    st.header("📊 P4 Capacity Comparison: CRU vs S&P Global (by Country)")

    year = st.slider("📅 Select Year", min_value=2010, max_value=2029, value=2021)

    cru_sheets = load_raw_p4_sheets(CRU_FILE)
    spg_sheets = load_raw_materials_data(SPG_FILE)

    cru_df = cru_sheets.get(CRU_SHEET)
    spg_df = spg_sheets.get(SPG_SHEET)

    if not isinstance(cru_df, pd.DataFrame) or not isinstance(spg_df, pd.DataFrame):
        st.error("Could not load required sheets.")
        return

    # Raw tables preview
    #st.subheader("🔍 Raw CRU Capacity Data (Summed by Country)")
    cru_raw = extract_cru_table(cru_df, year)
    #st.dataframe(cru_raw, use_container_width=True)

    #st.subheader("🔍 Raw S&P Global Capacity Data (Summed by Country)")
    spg_raw = extract_spg_table(spg_df, year)
    #st.dataframe(spg_raw, use_container_width=True)

    # Comparison table
    st.subheader("🧮 Comparative Table")
    df_cru = cru_raw.rename(columns={"Capacity": "CRU"})
    df_spg = spg_raw.rename(columns={"Capacity": "S&P Global"})

    merged = pd.merge(df_cru, df_spg, on="Country", how="outer").fillna(0)
    merged["Delta"] = merged["S&P Global"] - merged["CRU"]
    merged["% Difference"] = merged.apply(
        lambda row: (row["Delta"] / row["CRU"] * 100) if row["CRU"] else 0,
        axis=1
    )
    st.dataframe(merged, use_container_width=True)

    st.subheader("📊 Discrepancy Bar Chart: S&P Global - CRU")
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=merged["Country"],
        y=merged["Delta"],
        text=merged["Delta"].round(1),
        textposition="auto",
        marker_color=["crimson" if d < 0 else "seagreen" for d in merged["Delta"]],
        name="Delta (S&P Global - CRU)",
        hovertemplate='Country: %{x}<br>Delta: %{y}<br>' +
                      '<b style="color:crimson">Red</b>: CRU higher<br>' +
                      '<b style="color:seagreen">Green</b>: S&P Global higher'
    ))
    fig_bar.update_layout(
        height=400,
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font_color="white",
        xaxis_title="Country",
        yaxis_title="Delta in Capacity (kt/y)",
        legend=dict(title="Legend",
        orientation="h",  # horizontal
        yanchor="bottom",
        y=-0.5,           # move it below the chart
        xanchor="center",
        x=0.5
        ),
        showlegend=True
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # Country selection and year range comparison
    st.subheader("📈 Yearly Discrepancy for Selected Country")
    selected_country = st.selectbox("🌍 Choose Country to Explore Over Time", merged["Country"].unique())
    year_range = list(map(str, range(2010, 2030)))

    # Extract and clean full-year data
    cru_years = cru_df.copy()
    cru_years.columns = cru_years.columns.map(str)
    cru_years["Country"] = cru_years["Country"].apply(standardize_country_name)
    cru_years = cru_years.groupby("Country")[year_range].sum().reset_index()

    spg_years = spg_df.copy()
    spg_years.columns = spg_years.columns.map(str)
    spg_years = spg_years.rename(columns={"Geography": "Country"})
    spg_years["Country"] = spg_years["Country"].apply(standardize_country_name)
    spg_years = spg_years.groupby("Country")[year_range].sum().reset_index()

    # Get data for the selected country
    cru_country_series = cru_years[cru_years["Country"] == selected_country][year_range].sum()
    spg_country_series = spg_years[spg_years["Country"] == selected_country][year_range].sum()

    df_line = pd.DataFrame({
        "Year": list(map(int, year_range)),
        "CRU": cru_country_series.values,
        "S&P Global": spg_country_series.values
    })
    df_line["Delta"] = df_line["S&P Global"] - df_line["CRU"]

    # Plot lines over time
    fig_lines = go.Figure()
    fig_lines.add_trace(go.Scatter(x=df_line["Year"], y=df_line["CRU"], mode="lines+markers", name="CRU"))
    fig_lines.add_trace(go.Scatter(x=df_line["Year"], y=df_line["S&P Global"], mode="lines+markers", name="S&P Global"))
    fig_lines.update_layout(
        title="CRU vs S&P Global Capacity Over Time",
        xaxis_title="Year",
        yaxis_title="Capacity (kt/y)",
        height=400,
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font_color="white"
    )
    st.plotly_chart(fig_lines, use_container_width=True)

    # Plot delta over time
    fig_delta = go.Figure()
    fig_delta.add_trace(go.Scatter(x=df_line["Year"], y=df_line["Delta"], mode="lines+markers", name="Delta (S&P - CRU)"))
    fig_delta.update_layout(
        title="Discrepancy Over Time",
        xaxis_title="Year",
        yaxis_title="Delta (kt/y)",
        height=300,
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font_color="white"
    )
    st.plotly_chart(fig_delta, use_container_width=True)
    
    
    # New test
    st.subheader("📈 Yearly Discrepancy: China vs Rest of World")

    year_range = list(map(str, range(2010, 2030)))

    # Prepare yearly data for both CRU and SP Global
    cru_years = cru_df.copy()
    cru_years.columns = cru_years.columns.map(str)
    cru_years["Country"] = cru_years["Country"].apply(standardize_country_name)
    cru_years = cru_years.groupby("Country")[year_range].sum().reset_index()

    spg_years = spg_df.copy()
    spg_years.columns = spg_years.columns.map(str)
    spg_years = spg_years.rename(columns={"Geography": "Country"})
    spg_years["Country"] = spg_years["Country"].apply(standardize_country_name)
    spg_years = spg_years.groupby("Country")[year_range].sum().reset_index()

    # Default China vs Rest
    china_label = "China"
    all_countries = sorted(list(set(cru_years["Country"]).union(set(spg_years["Country"]))))
    default_rest = [c for c in all_countries if c != china_label]

    selected_rest = st.multiselect(
        "Select countries to include in 'Rest of the World'",
        options=default_rest,
        default=default_rest
    )

    # -- China Series --
    cru_china = cru_years[cru_years["Country"] == china_label][year_range].sum()
    spg_china = spg_years[spg_years["Country"] == china_label][year_range].sum()

    # -- Rest of World Series --
    cru_rest = cru_years[cru_years["Country"].isin(selected_rest)][year_range].sum()
    spg_rest = spg_years[spg_years["Country"].isin(selected_rest)][year_range].sum()

    # -- Build comparison dataframe --
    df_line = pd.DataFrame({
        "Year": list(map(int, year_range)),
        "CRU_China": cru_china.values,
        "SPG_China": spg_china.values,
        "CRU_Rest": cru_rest.values,
        "SPG_Rest": spg_rest.values
    })
    df_line["Delta_China"] = df_line["SPG_China"] - df_line["CRU_China"]
    df_line["Delta_Rest"] = df_line["SPG_Rest"] - df_line["CRU_Rest"]

    # -- Plot China vs Rest --
    fig_lines = go.Figure()
    fig_lines.add_trace(go.Scatter(
        x=df_line["Year"], y=df_line["CRU_China"], mode="lines+markers",
        name="CRU - China", line=dict(color="blue")
    ))
    fig_lines.add_trace(go.Scatter(
        x=df_line["Year"], y=df_line["SPG_China"], mode="lines+markers",
        name="S&P Global - China", line=dict(color="cyan")
    ))
    fig_lines.add_trace(go.Scatter(
        x=df_line["Year"], y=df_line["CRU_Rest"], mode="lines+markers",
        name="CRU - Rest of World", line=dict(color="green")
    ))
    fig_lines.add_trace(go.Scatter(
        x=df_line["Year"], y=df_line["SPG_Rest"], mode="lines+markers",
        name="S&P Global - Rest of World", line=dict(color="lightgreen")
    ))

    fig_lines.update_layout(
        title="China vs Rest of the World Capacity Over Time",
        xaxis_title="Year",
        yaxis_title="Capacity (kt/y)",
        height=450,
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font_color="white"
    )
    st.plotly_chart(fig_lines, use_container_width=True)

    # Plot delta (discrepancy) over time
    fig_delta = go.Figure()
    fig_delta.add_trace(go.Scatter(
        x=df_line["Year"], y=df_line["Delta_China"],
        mode="lines+markers", name="Delta China (S&P - CRU)", line=dict(color="cyan")
    ))
    fig_delta.add_trace(go.Scatter(
        x=df_line["Year"], y=df_line["Delta_Rest"],
        mode="lines+markers", name="Delta Rest (S&P - CRU)", line=dict(color="lightgreen")
    ))

    """fig_delta.update_layout(
        title="Discrepancy Over Time",
        xaxis_title="Year",
        yaxis_title="Delta (kt/y)",
        height=350,
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font_color="white"
    )
    st.plotly_chart(fig_delta, use_container_width=True)"""

    # -----------------------
    # 📄 Simplified Gap Table (Countries as rows, Years as columns)
    # -----------------------
    st.subheader("📄 Yearly Gap (Delta) Table: Countries vs Years")

    # --- Prepare data ---
    gap_rows = {}

    # --- China Delta ---
    gap_rows["China Delta"] = spg_china.values - cru_china.values

    # --- Rest of World Delta ---
    gap_rows["Rest of World Delta"] = spg_rest.values - cru_rest.values

    # --- Individual countries ---
    for country in selected_rest:
        cru_vals = cru_years[cru_years["Country"] == country][year_range].sum().values
        spg_vals = spg_years[spg_years["Country"] == country][year_range].sum().values
        delta = spg_vals - cru_vals
        gap_rows[f"{country} Delta"] = delta

    # --- Build the dataframe ---
    df_gap = pd.DataFrame(
        gap_rows, 
        index=list(map(int, year_range))
    ).T  # Transpose to have countries as rows

    st.dataframe(df_gap.style.format("{:,.0f}"), use_container_width=True)

    # --- Optional: Download button ---
    import io
    csv_buffer = io.StringIO()
    df_gap.to_csv(csv_buffer)
    st.download_button(
        label="📥 Download Gap Table as CSV",
        data=csv_buffer.getvalue(),
        file_name="china_vs_rest_gap_table.csv",
        mime="text/csv"
    )


    # -----------------------
    # 📝 Insights / Discussion (with delete option)
    # -----------------------
    import json
    import os

    st.subheader("📝 Insights & Discussion")

    INSIGHTS_FILE = "data/comparison_insights.json"

    # --- Load existing insights into session_state ---
    if "insights_data" not in st.session_state:
        if os.path.exists(INSIGHTS_FILE):
            with open(INSIGHTS_FILE, "r", encoding="utf-8") as f:
                st.session_state.insights_data = json.load(f)
        else:
            st.session_state.insights_data = []

    insights = st.session_state.insights_data

    # ---------- Add new insight form ----------
    with st.form("add_insight_form"):
        col1, col2 = st.columns(2)
        writer = col1.text_input("Your name", value="")
        message = col2.text_area("Your insight or takeaway", value="", height=100)
        submitted = st.form_submit_button("Add Insight")
        if submitted and writer.strip() and message.strip():
            insights.append({"writer": writer.strip(), "message": message.strip()})
            with open(INSIGHTS_FILE, "w", encoding="utf-8") as f:
                json.dump(insights, f, indent=2, ensure_ascii=False)
            st.success("Insight added.")
            # No rerun needed!

    # ---------- Display insights with delete ----------
    if insights:
        st.markdown("### 💬 Current Insights")
        for i, item in enumerate(insights[::-1]):  # newest first
            idx = len(insights) - 1 - i  # index in original list

            col_text, col_delete = st.columns([9, 1])
            with col_text:
                st.markdown(
                    f"""
                    <div style="background-color:#20232a; padding:10px; border-radius:10px;">
                        <strong>{item['writer']}</strong>: {item['message']}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col_delete:
                if st.button("X", key=f"delete_{idx}"):
                    st.session_state["delete_index"] = idx

    else:
        st.info("No insights added yet. Be the first to add one!")

    # ---------- Deletion confirmation ----------
    if "delete_index" in st.session_state:
        idx_to_delete = st.session_state["delete_index"]
        item = insights[idx_to_delete]
        st.warning(
            f"Are you sure you want to delete this insight by **{item['writer']}**: '{item['message']}'?"
        )
        col_confirm, col_cancel = st.columns(2)
        with col_confirm:
            if st.button("✅ Yes, delete"):
                insights.pop(idx_to_delete)
                with open(INSIGHTS_FILE, "w", encoding="utf-8") as f:
                    json.dump(insights, f, indent=2, ensure_ascii=False)
                st.success("Insight deleted.")
                del st.session_state["delete_index"]
                # No rerun needed!

        with col_cancel:
            if st.button("❌ Cancel"):
                del st.session_state["delete_index"]
