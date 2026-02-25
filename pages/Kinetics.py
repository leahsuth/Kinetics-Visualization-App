from src.parsing.parsing_data import process_data, standardize_data 
from src.figures.graph_csv import graph_from_csv
from src.figures.graph_xl import graph_from_xlsx
import streamlit as st
from streamlit import session_state as _state

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

# Remove state so they don't persist when new files are uploaded
if 'regression_models' in _state:
    _state.pop('regression_models')
    _state.pop('analytes')

if uploaded_file is None:
    st.info("Please Upload a file to begin")
    st.stop()

file_type = uploaded_file.name.split(".")[-1].lower()
with st.spinner("Loading data..."):
    df = process_data(uploaded_file)

#----Plotting----------------------------------------
if file_type == "csv":
    df.columns = df.columns.str.strip()
    samples = df["Sample Name"].str[:-4].unique()
    chosen_sample = st.sidebar.selectbox("Choose a sample to plot", samples)
    filtered_df = df[df["Sample Name"].str[:-4] == chosen_sample]
    st.success(f"Loaded {len(filtered_df)} rows for {chosen_sample}")
    try:
        graph_from_csv(filtered_df)
    except:
        st.stop() 
else:
    df = standardize_data(df)
    add_time(df, row=False, col=True)
    st.success(f"Loaded {len(df)} rows from Excel file")
    try:
        graph_from_xlsx(df)
    except:
        st.stop() 

#----Initial Rate----------------------------------------
st.divider()
st.write("# Initial Rate Calculations")

if 'regression_models' not in _state:
    st.warning('No models present!')
    st.stop()

models = _state['regression_models']
analytes = _state['analytes']

table_data = {
    "Analyte" : [sample for sample in analytes],
    "Correlation Coefficients" : [model.coef_.flat[0] for model in models]
}

st.table(table_data, border='horizontal')
