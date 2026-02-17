import streamlit as st
from src.page_styling.plate_selector import render_well_plate

st.set_page_config(layout="wide")

# CSS to make buttons more square/compact
selected_wells = render_well_plate()

st.write(f"{selected_wells}")
