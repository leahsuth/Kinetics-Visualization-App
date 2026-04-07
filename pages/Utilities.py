import streamlit as st
from src.page_styling.utilities_page.concentration import main_concentration_widget

st.logo(image='assets/Merck_Logo.png')
st.write("# Utility Functions")
st.markdown(
    "Common mathemtical calculations performed in a laboratory setting."
)

tab1, tab2, tab3, tab4 = st.tabs(["Concentration Calculations", "Dilutions", "Yield", "Purity"])
with tab1:
    main_concentration_widget()
