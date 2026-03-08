import io
import pandas as pd
import plotly.express as px
import streamlit as st
from src.parsing import parsing_data, parsing_initial_input
from src.page_styling.rate_information import rate_information
from src.figures.graph_xl import graph_from_xlsx

st.logo(image='assets/Merck_Logo.png')
st.write("# Kinetics Plotter")

#----Data Source----------------------------------------
if not st.session_state.get("hplc_file_bytes"):
    st.info("Please upload an HPLC file on the Experiment Setup page to begin.")
    st.stop()

if not st.session_state.get("cat_loading_df"):
    st.info("Please complete and save the Experiment Setup before viewing kinetics.")
    st.stop()

uploaded_file = io.BytesIO(st.session_state["hplc_file_bytes"])
uploaded_file.name = st.session_state.get("hplc_file_name", "hplc_data.xlsx")

with st.spinner("Loading data..."):
    df = parsing_data.process_data(uploaded_file)

#----Plotting----------------------------------------
# Get Initial Data from df
experiment_setup = st.session_state.get("cat_loading_df")
setup_df = parsing_initial_input.parse_cat_loading_file(experiment_setup)

df_time_and_rxn = parsing_data.add_timepoint_and_reaction(df, setup_df)
df_w_conditions = parsing_data.add_initial_input_conditions(df_time_and_rxn, setup_df)
final_df = parsing_data.standardize_data(df_w_conditions)


# Re-read bytes for process_first_line (BytesIO pointer was consumed above)
uploaded_file_for_first_line = io.BytesIO(st.session_state["hplc_file_bytes"])
uploaded_file_for_first_line.name = st.session_state.get("hplc_file_name", "hplc_data.xlsx")
first_line = parsing_data.process_first_line(uploaded_file_for_first_line)
st.session_state["first_line"] = first_line

st.success(f"Loaded {len(final_df)} rows from Excel file")

if "time" in final_df.columns:
    final_df["time"] = pd.to_numeric(final_df["time"], errors="coerce")

if "reaction" not in final_df.columns or "reactant" not in final_df.columns:
    st.error("Missing expected columns (reaction, reactant) after standardization.")
    st.stop()

reactions = final_df["reaction"].dropna().astype(str).unique().tolist()
selected_reactions = st.multiselect(
    "Select reactions to plot",
    reactions,
)
if not selected_reactions:
    st.warning("Please select at least one reaction.")
    st.stop()

df_plot = final_df[final_df["reaction"].astype(str).isin(selected_reactions)]

analytes = df_plot["reactant"].dropna().astype(str).unique().tolist()
analytes = sorted(analytes)
selected_analytes = st.multiselect(
    "Select analytes to plot",
    analytes,
    default=analytes if len(analytes) <= 8 else analytes[:5],
)
if not selected_analytes:
    st.warning("Please select at least one analyte.")
    st.stop()

df_plot = df_plot[df_plot["reactant"].astype(str).isin(selected_analytes)]

graph_from_xlsx(df_plot, selected_analytes)

#----Initial Rate----------------------------------------
st.divider()
st.write("# Initial Rate Calculations")

rate_reaction = st.selectbox("Reaction for rate calculation", selected_reactions, index=0)

df_rate = df_plot[df_plot["reaction"].astype(str) == str(rate_reaction)].copy()
if df_rate.empty:
    st.warning("No data available for rate calculation with current filters.")
    st.stop()

df_rate = df_rate.pivot_table(
    index="time",
    columns="reactant",
    values=select_meas,
    aggfunc="mean",
).reset_index()
df_rate = df_rate.rename(columns={"time": "Time"})
df_rate = df_rate.sort_values(by="Time")

rate_analytes = [a for a in selected_analytes if a in df_rate.columns]
if not rate_analytes:
    st.warning("Selected analytes are not available for rate calculation.")
    st.stop()

rate = rate_information(df_rate, rate_analytes)
if rate is not None:
    st.write(f"Calculated rate: {rate}")
