import streamlit as st
from src.page_styling.utilities_page.concentration import main_concentration_widget
from src.page_styling.utilities_page.dilution import dilution_widget
from src.page_styling.utilities_page.header import utility_header
from src.page_styling.utilities_page.enantiomeric_excee import ee_widget

st.set_page_config(
    page_title="Utilities",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.logo(image='assets/Merck_Logo.png')
with open("index.css", "r") as file:
    css = file.read()

st.html(f"<style>{css}</style>")
utility_header()

tab1, tab2, tab3, tab4 = st.tabs(["Concentration Calculations", "Dilutions", "Enantiomeric Excess", "Purity"])
with tab1:
    main_concentration_widget()
    # pass
with tab2:
    dilution_widget()
with tab3:
    ee_widget()
with tab4:
    st.write("Coming soon! :grin:")
