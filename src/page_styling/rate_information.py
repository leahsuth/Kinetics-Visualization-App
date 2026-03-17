import streamlit as st
import streamlit.components.v1 as components
from src.regression.rate_calculation import rate_calculation
import pandas as pd

def profile_picker(C0: float, Ce: float):
    if C0 > Ce:
        return 'decay'
    else:
        return 'growth'

def rate_information(df: pd.DataFrame, analytes: list, auto_pick: bool = True, k_input=None):
    analyte = st.selectbox('Select an Analyte', analytes, index=None)
    disable = analyte == None
    if disable:
        return None, {}

    if k_input is not None:
        k = float(k_input)
    else:
        k = st.number_input("Rate Constant: ", format="%0.01f", value=None, placeholder="Enter Rate Constant", key="rate_info_k")
        if k is None:
            return None, {}

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

    params = {"analyte": analyte, "k": k, "C0": C0, "Ce": Ce, "profile_type": profile_type}
    try:
        rate = rate_calculation(df, analyte, C0, Ce, k, profile_type)
        return rate, params
    except Exception as err:
        st.error(f"Error calculating rate: {err}")
        return None, params


