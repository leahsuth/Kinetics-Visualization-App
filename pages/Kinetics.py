from src.parsing.parsing_data import process_data, standardize_data 
from src.figures.graph_csv import graph_from_csv
from src.figures.graph_xl import graph_from_xlsx
import streamlit as st
from streamlit import session_state as _state
from src.page_styling.rate_information import rate_information

st.logo(image='assets/Merck_Logo.png')
st.write("# Kinetics Plotter")

#----File Upload----------------------------------------
with st.sidebar:
    st.header("Filters")
    uploaded_file = st.file_uploader(
        "Choose a kinetics data file",
        #added ability to upload both csv and xlsx files
        type=["csv", "xlsx"],
        help="Upload a CSV or Excel (ChemStation) kinetics file.",
    )


if uploaded_file is None:
    st.info("Please Upload a file to begin")
    st.stop()

file_type = uploaded_file.name.split(".")[-1].lower()
with st.spinner("Loading data..."):
    df = process_data(uploaded_file)


#----Plotting / Analyte Selection----------------------------------------
if file_type == "csv":
    analytes = st.multiselect("Select an analyte", df.drop(columns=['Sample Name', 'Time']).columns)

    if len(analytes) == 0:
        st.warning("Please select at least one analyte to plot.")
        st.stop()
    df.columns = df.columns.str.strip()
    samples = df["Sample Name"].str[:-4].unique()
    chosen_sample = st.sidebar.selectbox("Choose a sample to plot", samples)
    filtered_df = df[df["Sample Name"].str[:-4] == chosen_sample]
    st.success(f"Loaded {len(filtered_df)} rows for {chosen_sample}")
    try:
        graph_from_csv(filtered_df, analytes)
    except Exception as err:
        st.error(f"Error plotting data: {err}")
        st.stop() 
else:
    df = standardize_data(df)
    st.success(f"Loaded {len(df)} rows from Excel file")
    sample_col = "Reaction" if "Reaction" in df.columns else "Sample"
    if sample_col in df.columns:
        samples = df[sample_col].unique()
        selected_samples = st.multiselect(
            "Select samples to plot",
            samples,
            default=list(samples) if len(samples) <= 10 else list(samples[:5]),
        )
        if not selected_samples:
            st.warning("Please select at least one sample.")
            st.stop()

    reactants = df["Reactant"].unique()
    select_reactants = st.multiselect("Select reactants to plot", reactants, default=list(reactants))
    try:
        graph_from_xlsx(df, analytes)
    except:
        st.stop() 

#----Initial Rate----------------------------------------
st.divider()
st.write("# Initial Rate Calculations")


rate = rate_information(df, analytes)
st.write(rate)

