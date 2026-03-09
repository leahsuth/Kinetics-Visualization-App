import streamlit as st
import streamlit.components.v1 as components
from src.regression.rate_calculation import rate_calculation
import pandas as pd

def rate_information(df: pd.DataFrame, analytes: list):
    analyte = st.selectbox('Select an Analyte', analytes, index=None)
    disable = analyte == None
    C0 = st.number_input("Initial Concentration: ", min_value=0, disabled=disable)
    Ce = st.number_input("Equilibrium Concentration: ", min_value=0, disabled=disable)
    k = st.number_input("Rate Constant: ", min_value=0, disabled=disable)
    profile_type = st.radio(
        "Profile Type: ",
        ['decay', 'growth'],
        disabled=disable
    )
    try:
        rate = rate_calculation(df, analyte, C0, Ce, k, profile_type)
        return rate
    except Exception as err:
        st.error(f"Error calculating rate: {err}")


