import io
import pandas as pd
from src.parsing import parsing_data, parsing_initial_input
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

with st.spinner("Loading data..."):
    df = parsing_data.process_data(uploaded_file)

#----Plotting----------------------------------------
# Get Initial Data from df
experiment_setup = st.session_state.get("cat_loading_df")
setup_df = parsing_initial_input.parse_cat_loading_file(experiment_setup)

df_sorted = parsing_data.sort_wells_by_time_blocks(df, setup_df)
df_time_and_rxn = parsing_data.time_and_rxn(df_sorted, setup_df)
final_df = parsing_data.standardize_data(df_time_and_rxn)

# Merge annotations onto standardized result (one row per reaction)
lookup = setup_df.drop_duplicates(subset=["Reaction"], keep="first").drop(
    columns=["time", "well"], errors="ignore"
)

final_df = final_df.merge(
    lookup, left_on="reaction", right_on="Reaction", how="left"
)

if "Reaction" in final_df.columns and "reaction" in final_df.columns:
    final_df = final_df.drop(columns=["Reaction"], errors="ignore")

# Re-read bytes for process_first_line (BytesIO pointer was consumed above)
uploaded_file_for_first_line = io.BytesIO(st.session_state["hplc_file_bytes"])
first_line = parsing_data.process_first_line(uploaded_file_for_first_line)
st.session_state["first_line"] = first_line

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