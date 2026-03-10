import streamlit as st
import streamlit.components.v1 as components
from src.regression.rate_calculation import rate_calculation
import pandas as pd

def profile_picker(C0: float, Ce: float):
    if C0 > Ce:
        return 'decay'
    else:
        return 'growth'

def rate_information(df: pd.DataFrame, analytes: list, auto_pick: bool = True):
    analyte = st.selectbox('Select an Analyte', analytes, index=None)
    disable = analyte == None
    if disable:
        return

    k = st.number_input("Rate Constant: ", format="%0.01f", value=None, placeholder="Enter Rate Constant")
    if k is None:
        return

    if auto_pick:
        C0 = df[analyte].iloc[0]
        Ce = df[analyte].iloc[-1]
        profile_type = profile_picker(C0, Ce)
    else:
        C0 = st.number_input("Initial Concentration: ", min_value=0, disabled=disable)
        Ce = st.number_input("Equilibrium Concentration: ", min_value=0, disabled=disable)
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


