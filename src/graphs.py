import pandas as pd
import streamlit as st

def area_chart(analytes: list, df: pd.DataFrame):
    if len(analytes) == 0:
        st.write("### Please choose analyte(s) to plot")
    
    st.scatter_chart(df, x="Time", y=analytes)

def graph_from_csv(df: pd.DataFrame):
    col1, col2 = st.columns(2)

    with col1:
        analytes = st.multiselect(
            "Select Analytes", 
            df.drop(columns=["Sample Name", "Time"]).columns)
    with col2:
        area_chart(analytes, df)
