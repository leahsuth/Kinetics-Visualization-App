import io
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from src.parsing.parsing_data import process_streamlit
from src.page_styling.rate_information import rate_information, profile_picker
from src.figures.graph_xl import graph_from_xlsx
from src.parsing.plotting_process import plot_process
from src.regression.rate_calculation import rate_calculation, fit_kinetics_and_return_params, exp_func
from src.page_styling.report_generator import generate_report_pdf

st.logo(image='assets/Merck_Logo.png')
st.write("# Kinetics Plotter")


# ----Data Source----------------------------------------
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

# ----Plotting----------------------------------------
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

time_units = ["hours", "minutes", "seconds", "days"]
default_time_unit = st.session_state.get("_kinetics_time_unit", "hours")
if default_time_unit not in time_units:
    default_time_unit = "hours"

time_unit = st.selectbox(
    "Time units",
    options=time_units,
    index=time_units.index(default_time_unit),
)
st.session_state["_kinetics_time_unit"] = time_unit

# ----Pre-processing for plotting----------------------------------------
df_plot, selected_measurements = plot_process(df_plot,
                                              selected_reactions,
                                              selected_analytes,
                                              )

# ----Multiple plots (per-reaction, grid layout)----------------------
color_options = [c for c in ["reactant", "reaction"] if c in df_plot.columns]
default_color_by = st.session_state.get("_kinetics_color_by", "reactant")
if default_color_by not in color_options:
    default_color_by = color_options[0] if color_options else "reactant"

color_by = st.radio(
    "Color by:",
    color_options or ["reactant"],
    index=(color_options.index(default_color_by)
           if color_options and default_color_by in color_options else 0),
)
st.session_state["_kinetics_color_by"] = color_by

chart_type = st.radio(
    "Chart type",
    ["Scatter", "Line"],
    horizontal=True,
    key="time_series_chart_type",
)

multi_plot_choice = st.radio(
    "Visualize reaction data in multiple plots?",
    ["No", "Yes"],
    index=0,
    horizontal=True,
)

reactions_for_plots: list[str] = []
if multi_plot_choice == "Yes":
    reactions_for_plots = st.multiselect(
        "Reactions to display as separate plots.",
        options=selected_reactions,
        default=None,
    )

if reactions_for_plots:
    # Render up to two plots per row
    for i in range(0, len(reactions_for_plots), 2):
        row_reactions = reactions_for_plots[i : i + 2]
        cols = st.columns(len(row_reactions))
        for col, rxn in zip(cols, row_reactions):
            with col:
                df_rxn = df_plot[df_plot["reaction"].astype(str) == str(rxn)]
                if not df_rxn.empty:
                    fig = graph_from_xlsx(
                        df=df_rxn,
                        select_meas=selected_measurements,
                        color_select=color_by,
                        chart_type=chart_type,
                        title_suffix=f"Reaction {rxn}",
                        time_unit=time_unit,
                    )
                    st.plotly_chart(fig, use_container_width=True)

# plot remaining reactions in a single plot
remaining_reactions = [r for r in selected_reactions
                       if r not in reactions_for_plots]
if remaining_reactions:
    df_remaining = df_plot[df_plot["reaction"].
                           astype(str).isin(remaining_reactions)]
    fig = graph_from_xlsx(
        df=df_remaining,
        select_meas=selected_measurements,
        color_select=color_by,
        chart_type=chart_type,
        time_unit=time_unit,
    )
    st.plotly_chart(fig, use_container_width=True)

first_line = st.session_state["first_line"]
st.caption(first_line)

# ----Initial Rate----------------------------------------
st.divider()
st.write("# Initial Rate Calculations")

rate_reaction = st.selectbox("Reaction for rate calculation",
                             selected_reactions,
                             index=0)

df_rate = df_plot[df_plot["reaction"].astype(str) == str(rate_reaction)].copy()
if df_rate.empty:
    st.warning("No data available for rate calculation with current filters.")
    st.stop()

df_rate = df_rate.pivot_table(
    index="time",
    columns="reactant",
    values=selected_measurements,
    aggfunc="mean",
).reset_index()
df_rate = df_rate.rename(columns={"time": "Time"})
df_rate = df_rate.sort_values(by="Time")

rate_analytes = [a for a in selected_analytes if a in df_rate.columns]
if not rate_analytes:
    st.warning("Selected analytes are not available for rate calculation.")
    st.stop()

k_constant = st.number_input("Rate constant (k)", value = 0.1, min_value = 1e-10, format = "%0.2f", key = "k_rate")
auto_pick = st.radio("Should the rate parameters be automatically selected?", ['auto', 'manual'])

rate, rate_params = rate_information(df_rate, rate_analytes, auto_pick == 'auto', k_input = k_constant)

#Plot history
st.divider()
st.write("## Rate Plots")

if "kinetics_plot_history" not in st.session_state:
    st.session_state["kinetics_plot_history"] = []
if "kinetics_plotted_keys" not in st.session_state:
    st.session_state["kinetics_plotted_keys"] = set()

# Controls: reaction, analyte, profile, plus summary
st.write("### Controls")


def build_rate_summary(df_rate: pd.DataFrame, analytes: list, k: float) \
                       -> pd.DataFrame:
    """Calculate rate for each analyte and return summary DataFrame."""
    rows = []
    for analyte in analytes:
        if analyte not in df_rate.columns:
            rows.append({"Analyte": analyte, "Rate": None})
            continue
        C0 = df_rate[analyte].iloc[0]
        Ce = df_rate[analyte].iloc[-1]
        profile_type = profile_picker(C0, Ce)
        try:
            r = rate_calculation(df_rate, analyte, C0, Ce, k, profile_type)
        except Exception:
            r = None
        rows.append({"Analyte": analyte, "Rate": r})
    return pd.DataFrame(rows)


summary_df = build_rate_summary(df_rate, rate_analytes, k_constant)
st.dataframe(summary_df, use_container_width=True)

# Exponential curve fit + auto-add when new reaction or analyte is selected
choose_analyte = rate_params.get("analyte")
new_plot_added = False

if choose_analyte and choose_analyte in df_rate.columns:
    single_df = df_rate[["Time", choose_analyte]].copy()
    single_df["Time"] = pd.to_numeric(single_df["Time"], errors="coerce")
    single_df[choose_analyte] = pd.to_numeric(single_df[choose_analyte],
                                              errors="coerce")
    single_df = single_df.dropna(subset=["Time", choose_analyte]).\
        sort_values("Time").reset_index(drop=True)

    if len(single_df) >= 3:
        C0_init = float(single_df[choose_analyte].iloc[0])
        Ce_init = float(single_df[choose_analyte].iloc[-1])
        default_profile = profile_picker(C0_init, Ce_init)
        profile_type = st.radio(
            "Profile type for fit",
            ["growth", "decay"],
            index=0 if default_profile == "growth" else 1,
            key="curve_profile",
            help="Growth: C = Ce + (C0-Ce)*exp(-kt). Decay: C = C0*exp(-kt)+Ce.",
        )
        result = fit_kinetics_and_return_params(
            single_df, choose_analyte, C0_init,
            Ce_init, k_constant, profile_type
        )
        if result is not None:
            C0, Ce, k = result[0], result[1], result[2]
            par = {"C0": C0, "Ce": Ce, "k": k}
            t_min = float(single_df["Time"].min())
            t_max = float(single_df["Time"].max())
            t_fine = np.linspace(t_min, t_max, 100)
            y_fit = exp_func(C0, Ce, k, t_fine, profile_type)

            t_rate = 0
            if profile_type == "growth":
                rate_val = (par["Ce"] - par["C0"]) * par["k"] * np.exp(-t_rate * par["k"])
            else:
                rate_val = par["C0"] * par["k"] * np.exp(-t_rate * par["k"])

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=single_df["Time"],
                    y=single_df[choose_analyte],
                    mode="markers",
                    name="data",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=t_fine,
                    y=y_fit,
                    mode="lines",
                    name="fitted curve",
                    line=dict(color="#E53935", width=2),
                )
            )
            fig.update_layout(
                title=f"{choose_analyte} with exponential fit",
                xaxis_title=f"Time ({time_unit})",
                yaxis_title=selected_measurements,
                width=400,
                height=250,
            )
            # Add to history when reaction, analyte, or profile has changed
            plot_key = (rate_reaction, choose_analyte, profile_type)
            if plot_key not in st.session_state["kinetics_plotted_keys"]:
                rate_table = pd.DataFrame([
                    {
                        "Reaction": rate_reaction,
                        "Analyte": choose_analyte,
                        "Profile": profile_type,
                        "Rate": rate_val,
                        "C0": par["C0"],
                        "Ce": par["Ce"],
                        "k": par["k"],
                    }
                ])
                st.session_state["kinetics_plot_history"].append({
                    "reaction": rate_reaction,
                    "analyte": choose_analyte,
                    "profile_type": profile_type,
                    "fig": fig,
                    "rate_table": rate_table,
                    "selected_measurements": selected_measurements,
                })
                st.session_state["kinetics_plotted_keys"].add(plot_key)
                new_plot_added = True
    else:
        st.warning(f"Not enough data points for {choose_analyte}.")
else:
    st.info("Select an analyte above to generate a plot.")

# Displays plot and corresponding rate table side by side
if st.session_state["kinetics_plot_history"]:
    if new_plot_added:
        st.success("New plot added. Change reaction or analyte to add another.")
    for i, item in enumerate(reversed(st.session_state["kinetics_plot_history"])):
        st.write(f"---")
        st.caption(f"**{item['reaction']}** — {item['analyte']} ({item['profile_type']})")
        col_plot, col_table = st.columns([3, 1])
        with col_plot:
            st.plotly_chart(item["fig"], use_container_width=True)
        with col_table:
            st.dataframe(item["rate_table"], use_container_width=True, hide_index=True)
    if st.button("Clear all plots", key="clear_plots"):
        st.session_state["kinetics_plot_history"] = []
        st.session_state["kinetics_plotted_keys"] = set()
        st.rerun()

st.divider()
st.subheader("Export Report")
try:
    color_by = st.session_state.get("_kinetics_color_by", "reactant")
    select_meas = (
        selected_measurements
        if isinstance(selected_measurements, str)
        else (selected_measurements[0] if selected_measurements else "area")
    )
    pdf_bytes = generate_report_pdf(
        df=df_plot,
        select_meas=select_meas,
        color_by=color_by,
        experiment_setup=st.session_state.get("experiment_setup", {}),
        hplc_file_name=st.session_state.get("hplc_file_name", "-"),
        rate_reaction=rate_reaction,
        rate_value=rate,
        rate_params=rate_params or {},
    )
    st.download_button(
        "Download Report (.pdf)",
        data=pdf_bytes,
        file_name="kinetics_report.pdf",
        mime="application/pdf",
        use_container_width=True,
        type="primary",
    )
except Exception as e:
    st.warning(f"PDF export unavailable: {e}")
