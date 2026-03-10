import io
import pandas as pd
from src.parsing.parsing_data import process_streamlit
from src.figures import graph_xl
import streamlit as st
from src.page_styling.rate_information import rate_information
from src.figures.graph_xl import graph_from_xlsx
from src.parsing.plotting_process import plot_process

st.logo(image='assets/Merck_Logo.png')
st.write("# Kinetics Plotter")

#----Data Source----------------------------------------
if "hplc_file_bytes" not in st.session_state:
    st.info("Please upload an HPLC file on the Experiment Setup page to begin.")
    st.stop()

if "cat_loading_df" not in st.session_state:
    st.info("Please complete and save the Experiment Setup before viewing kinetics.")
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


# Pre-processing for plotting
df_plot, select_meas = plot_process(df_plot, selected_reactions, selected_analytes)

graph_from_xlsx(df_plot, selected_reactions, selected_analytes, select_meas)

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
