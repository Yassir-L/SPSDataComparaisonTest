# main_app.py

import streamlit as st
from modules.p4_data_module import show as show_p4_data
from modules.supply_demand_module import show as show_supply_demand
from modules.raw_materials_data_module import show as show_raw_materials_data
from modules.raw_materials_analysis_module import show as show_raw_materials_analytics
from modules.compare_sources_module import show as show_comparative_analysis

st.set_page_config(layout="wide", page_title="P4 Market Dashboard")

st.sidebar.title("🔍 Navigation")
page = st.sidebar.radio("Go to:", [
    "🆚 Compare CRU vs S&PG",
    "📊 P4 Supply&Demand",
    "📄 Raw Materials Data",
    "📊 Raw Materials Analytics",
    "📄 N&PG P4 Data"
])

if page == "🆚 Compare CRU vs S&PG":
    show_comparative_analysis()
elif page == "📊 P4 Supply&Demand":
    show_supply_demand()
elif page == "📄 CRU P4 Raw Data":
    show_raw_materials_data()
elif page == "📊 Raw Materials Analytics":
    show_raw_materials_analytics()
elif page == "📄 N&PG P4 Data":
    show_p4_data()

st.sidebar.markdown("🆕 Version: May 07 Update")
