import io
import pandas as pd
import plotly.express as px
import streamlit as st
from src.parsing import parsing_data, parsing_initial_input
from src.page_styling.rate_information import rate_information

st.logo(image='assets/Merck_Logo.png')
st.write("# Kinetics Plotter")

#----Data Source----------------------------------------
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
df_with_conditions = parsing_data.add_initial_input_conditions(df_time_and_rxn, setup_df)
final_df = parsing_data.standardize_data(df_with_conditions)

# Re-read bytes for process_first_line (BytesIO pointer was consumed above)
uploaded_file_for_first_line = io.BytesIO(st.session_state["hplc_file_bytes"])
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

df_plot = final_df[final_df["reaction"].astype(str).isin(selected_reactions)].copy()

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

df_plot = df_plot[df_plot["reactant"].astype(str).isin(selected_analytes)].copy()

exclude_cols = {"reaction", "reactant", "time", "well", "plate_well", "role", "notes"}
preferred = [c for c in ["peak_area", "peak_ap"] if c in df_plot.columns]
measurement_cols = preferred[:]
if not measurement_cols:
    candidates = [c for c in df_plot.columns if c not in exclude_cols]
    for c in candidates:
        coerced = pd.to_numeric(df_plot[c], errors="coerce")
        if coerced.notna().any():
            measurement_cols.append(c)
if not measurement_cols:
    st.error("No numeric measurement columns found for plotting.")
    st.stop()

select_meas = st.selectbox("Select measurement to plot", measurement_cols)
df_plot[select_meas] = pd.to_numeric(df_plot[select_meas], errors="coerce")

color_options = [c for c in ["reactant", "reaction"] if c in df_plot.columns]
color_select = st.radio("Color by:", color_options, horizontal=True)

chart_type = st.radio("Chart type", ["Scatter", "Line"], horizontal=True)

fig_kwargs = dict(
    width=1200,
    height=500,
    hover_data={c: True for c in df_plot.columns},
)

if chart_type == "Line":
    fig = px.line(
        df_plot.sort_values(by=["reaction", "reactant", "time"]),
        x="time",
        y=select_meas,
        color=color_select,
        markers=True,
        **fig_kwargs,
    )
else:
    fig = px.scatter(
        df_plot,
        x="time",
        y=select_meas,
        color=color_select,
        **fig_kwargs,
    )

fig.update_layout(
    title=dict(
        text=f"{select_meas} vs. time",
        font=dict(size=28),
        x=0.5,
        xanchor="center",
        y=0.95,
        yanchor="top",
    )
)

st.plotly_chart(fig, use_container_width=True)
st.caption(first_line)

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
