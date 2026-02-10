from src.graphs import graph_from_csv
import pandas as pd
import streamlit as st

st.write("# Kinetics Plotter")

with st.sidebar:
    st.header("Filters")
    uploaded_file = st.file_uploader(
        "Choose a kinetics CSV file",
        type=["csv"],
        help="Upload a CSV with columns: Sample Name, Time, and analyte columns.",
    )
    chosen_sample = None
    filtered_df = None
    if uploaded_file is not None:
        with st.spinner("Loading data..."):
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip()
            samples = df["Sample Name"].str[:-4].unique()
            chosen_sample = st.selectbox("Choose a sample to plot", samples)
            filtered_df = df[df["Sample Name"].str[:-4] == chosen_sample]
        st.success(f"Loaded {len(filtered_df)} rows for {chosen_sample}")

if filtered_df is not None:
    graph_from_csv(filtered_df)