from src.graphs import graph_from_csv
import pandas as pd
import streamlit as st


st.write("# Upload a file, produce a graph")

uploaded_file = st.file_uploader("File goes here", accept_multiple_files=False)

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()
    samples = df['Sample Name'].str[:-4].unique()
    chosen_sample = st.selectbox("Choose a sample to plot", samples)
    filtered_df = df[df['Sample Name'].str[:-4] == chosen_sample]
    graph_from_csv(filtered_df)
