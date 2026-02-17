import streamlit as st
from src.page_styling.plate_selector import render_well_plate

st.set_page_config(layout="wide")

n_rows = st.number_input("Number of Rows", min_value=1, max_value=12, value=1)
n_cols = st.number_input("Number of Columns", min_value=1, max_value=12, value=1)

# CSS to make buttons more square/compact
selected_wells = render_well_plate(n_rows, n_cols)

st.write(f"{selected_wells}")
