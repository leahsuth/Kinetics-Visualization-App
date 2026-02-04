import pandas as pd
import streamlit as st

import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

st.set_page_config(layout = "wide")

def graph_from_csv(df: pd.DataFrame):
  col1, col2 = st.columns(2)

  with col1:
    analytes = st.multiselect(
               "Select Analytes", 
               df.drop(columns=["Sample Name", "Time"]).columns)
  with col2:
    if len(analytes) == 0:
      st.write("### Please choose analyte(s) to plot")
      return

    #melt dataframe to plot multiple analytes
    melted_df = df.melt(id_vars = ["Time"], value_vars = analytes,
                        var_name = "Analyte", value_name = "Concentration")
    #plotly to make interactive
    fig = px.scatter(melted_df, x='Time', y="Concentration", color= "Analyte",
                     hover_data = {"Time": True, "Concentration": True,
                     "Analyte": True}, title= f"Concentration vs. Time",
                     width = 1400, height = 800)

    st.plotly_chart(fig, use_container_width = True)
