from src.parsing import parsing_data, parsing_initial_input
from src.figures import graph_csv, graph_xl
import streamlit as st
from streamlit import session_state as _state

st.logo(image='assets/Merck_Logo.png')
st.write("# Kinetics Plotter")

#----File Upload----------------------------------------
with st.sidebar:
    st.header("Filters")
    uploaded_file = st.file_uploader(
        "Choose a kinetics data file",
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
    df = parsing_data.process_data(uploaded_file)

#----Plotting----------------------------------------
if file_type == "csv":
    df.columns = df.columns.str.strip()
    samples = df["Sample Name"].str[:-4].unique()
    chosen_sample = st.sidebar.selectbox("Choose a sample to plot", samples)
    filtered_df = df[df["Sample Name"].str[:-4] == chosen_sample]
    st.success(f"Loaded {len(filtered_df)} rows for {chosen_sample}")
    try:
        graph_csv.graph_from_csv(filtered_df)
    except Exception:
        st.stop()

elif file_type in ("xlsx", "xls"):
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

    # Save the first line to Streamlit session state before plotting,
    # so `graph_from_xlsx` can safely read it.
    first_line = parsing_data.process_first_line(uploaded_file)
    st.session_state["first_line"] = first_line

    st.success("Loaded Excel file.")
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