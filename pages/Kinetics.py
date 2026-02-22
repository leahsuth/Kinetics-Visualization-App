from src.parsing.parsing_data import process_data, standardize_data, add_time
from src.figures.graphs import graph_from_csv, graph_from_xlsx
import streamlit as st

st.logo(image='assets/Merck_Logo.png')
st.write("# Kinetics Plotter")

with st.sidebar:
    st.header("Filters")
    uploaded_file = st.file_uploader(
        "Choose a kinetics data file",
        #added ability to upload both csv and xlsx files
        type=["csv", "xlsx"],
        help="Upload a CSV or Excel (ChemStation) kinetics file.",
    )

if uploaded_file is not None:
    file_type = uploaded_file.name.split(".")[-1].lower()
    with st.spinner("Loading data..."):
        df = process_data(uploaded_file)

    if file_type == "csv":
        df.columns = df.columns.str.strip()
        samples = df["Sample Name"].str[:-4].unique()
        chosen_sample = st.sidebar.selectbox("Choose a sample to plot", samples)
        filtered_df = df[df["Sample Name"].str[:-4] == chosen_sample]
        st.success(f"Loaded {len(filtered_df)} rows for {chosen_sample}")
        graph_from_csv(filtered_df)
    else:
        df = standardize_data(df)
        add_time(df, row=False, col=True)
        st.success(f"Loaded {len(df)} rows from Excel file")
        graph_from_xlsx(df)
