import io
import pandas as pd
from src.parsing.parsing_data import process_streamlit
from src.figures import graph_xl
import streamlit as st
from streamlit import session_state as _state

st.logo(image='assets/Merck_Logo.png')
st.write("# Kinetics Plotter")

# Remove state so they don't persist when new files are uploaded
if 'regression_models' in _state:
    _state.pop('regression_models')
    _state.pop('analytes')

#----File Upload----------------------------------------
if not st.session_state.get("hplc_file_bytes"):
    st.info("Please upload an HPLC file on the Experiment Setup page to begin.")
    st.stop()

if not isinstance(st.session_state.get("cat_loading_df"), pd.DataFrame):
    st.warning("Please complete and save the Experiment Setup before viewing kinetics.")
    st.stop()

uploaded_file = io.BytesIO(st.session_state["hplc_file_bytes"])
uploaded_file.name = st.session_state.get("hplc_file_name", "hplc_data.xlsx")

with st.spinner("Loading data..."):
    # Get Initial Data from df
    experiment_setup = st.session_state.get("cat_loading_df")
    final_df, first_line = process_streamlit(experiment_setup,
                                             uploaded_file)
    st.session_state["first_line"] = first_line

#----Plotting----------------------------------------
st.success("Loaded HPLC file.")
graph_xl.graph_from_xlsx(final_df)

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