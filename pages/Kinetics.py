from src.parsing import parsing_data, parsing_initial_input
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
        df = parsing_data.process_data(uploaded_file)

    if file_type == "csv":
        df.columns = df.columns.str.strip()
        samples = df["Sample Name"].str[:-4].unique()
        chosen_sample = st.sidebar.selectbox("Choose a sample to plot", samples)
        filtered_df = df[df["Sample Name"].str[:-4] == chosen_sample]
        st.success(f"Loaded {len(filtered_df)} rows for {chosen_sample}")
        graph_from_csv(filtered_df)
    else:
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

        st.success(f"Loaded {len(final_df)} rows from Excel file")
        graph_from_xlsx(final_df)
