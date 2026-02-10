import streamlit as st

st.set_page_config(
    page_title="Merck Kinetics Application",
    page_icon="📊",
    layout="wide",
)

st.markdown("# Merck Kinetics Application")
st.markdown(
    "Upload kinetics CSV data, select a reaction, and visualize concentration over time."
)
st.page_link("pages/Kinetics.py", label="→ Upload & Plot Data", icon="📈")