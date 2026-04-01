import io
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from src.parsing.parsing_data import process_streamlit
from src.page_styling.rate_information import profile_picker
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
# INFO: peak_area vs AP is being set here
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
    index=1,
    horizontal=True,
)

reactions_for_plots: list[str] = []
if multi_plot_choice == "Yes":
    reactions_for_plots = st.multiselect(
        "Reactions to display as separate plots.",
        options=selected_reactions,
        default=selected_reactions,
    )

reaction_plot_data = []
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

# Collect one entry per selected reaction for the PDF report
for rxn in selected_reactions:
    df_rxn = df_plot[df_plot["reaction"].astype(str) == str(rxn)]
    if not df_rxn.empty:
        reaction_plot_data.append({
            "reaction": rxn,
            "df": df_rxn,
            "select_meas": selected_measurements,
            "color_by": color_by,
        })

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

first_line = st.session_state.get("first_line", "")
st.caption(first_line)

# ----Initial Rate----------------------------------------
st.divider()
st.write("# Initial Rate Calculations")

k_constant = st.number_input(
    "Rate constant (k)", value=0.1, min_value=1e-10, format="%0.2f", key="k_rate"
)

if "kinetics_plot_history" not in st.session_state:
    st.session_state["kinetics_plot_history"] = []
if "kinetics_plotted_keys" not in st.session_state:
    st.session_state["kinetics_plotted_keys"] = set()
if "kinetics_clear_counter" not in st.session_state:
    st.session_state["kinetics_clear_counter"] = 0


def build_rate_summary(df_pivot: pd.DataFrame, analytes: list, k: float) -> pd.DataFrame:
    """Calculate rate for each analyte and return summary DataFrame."""
    rows = []
    for analyte in analytes:
        if analyte not in df_pivot.columns:
            rows.append({"Analyte": analyte, "Rate": None})
            continue
        C0 = df_pivot[analyte].iloc[0]
        Ce = df_pivot[analyte].iloc[-1]
        profile_type = profile_picker(C0, Ce)
        try:
            r = rate_calculation(df_pivot, analyte, C0, Ce, k, profile_type)
        except Exception:
            r = None
        rows.append({"Analyte": analyte, "Rate": r})
    return pd.DataFrame(rows)


# Compute pivot tables once per reaction and reuse for both summary and fit plots
df_rate_by_rxn: dict = {}
for rxn in selected_reactions:
    df_rxn = df_plot[df_plot["reaction"].astype(str) == str(rxn)]
    if not df_rxn.empty:
        df_rate_by_rxn[rxn] = (
            df_rxn.pivot_table(
                index="time", columns="reactant", values="peak_ap", aggfunc="mean"
            )
            .reset_index()
            .sort_values("time")
        )

# ---- Rate Summary (Controls table per reaction) ----
st.write("### Rate Summary")
rate_summaries = []
for rxn in selected_reactions:
    df_pivot = df_rate_by_rxn.get(rxn)
    if df_pivot is None:
        continue
    rxn_analytes = [a for a in selected_analytes if a in df_pivot.columns]
    if not rxn_analytes:
        continue
    summary = build_rate_summary(df_pivot, rxn_analytes, k_constant)
    st.write(f"**Reaction {rxn}**")
    st.dataframe(summary, use_container_width=True)
    rate_summaries.append({"reaction": rxn, "summary_df": summary})

# ---- Fit Plots ----
st.divider()
st.write("## Rate Plots")

generate_plots = st.radio(
    "Generate exponential fit plots?", ["No", "Yes"], horizontal=True
)

if generate_plots == "Yes":
    manual_profile = st.checkbox(
        "Manually select growth/decay profile per analyte",
        value=False,
        key="manual_profile_select",
    )
    for rxn in selected_reactions:
        df_pivot = df_rate_by_rxn.get(rxn)
        if df_pivot is None:
            continue
        rxn_analytes = [a for a in selected_analytes if a in df_pivot.columns]
        if not rxn_analytes:
            continue
        st.write(f"**Reaction {rxn}**")
        _cc = st.session_state["kinetics_clear_counter"]
        chosen_analytes = st.multiselect(
            f"Analytes to fit — Reaction {rxn}",
            rxn_analytes,
            key=f"fit_analytes_{rxn}_{_cc}",
        )
        for analyte in chosen_analytes:
            single_df = (
                df_pivot[["time", analyte]]
                .copy()
                .dropna(subset=["time", analyte])
                .sort_values("time")
                .reset_index(drop=True)
            )
            if len(single_df) < 3:
                st.warning(f"Not enough data points for {analyte}.")
                continue
            C0_init = float(single_df[analyte].iloc[0])
            Ce_init = float(single_df[analyte].iloc[-1])
            default_profile = profile_picker(C0_init, Ce_init)
            if manual_profile:
                profile_type = st.radio(
                    f"Profile — Reaction {rxn} / {analyte}",
                    ["growth", "decay"],
                    index=0 if default_profile == "growth" else 1,
                    key=f"profile_{rxn}_{analyte}_{_cc}",
                    horizontal=True,
                    help="Growth: C = Ce + (C0-Ce)*exp(-kt). Decay: C = C0*exp(-kt)+Ce.",
                )
            else:
                profile_type = default_profile
            result = fit_kinetics_and_return_params(
                single_df, analyte, C0_init, Ce_init, k_constant, profile_type
            )
            if result is not None:
                C0, Ce, k_fit = result[0], result[1], result[2]
                t_fine = np.linspace(
                    float(single_df["time"].min()),
                    float(single_df["time"].max()),
                    100,
                )
                y_fit = exp_func(C0, Ce, k_fit, t_fine, profile_type)
                if profile_type == "growth":
                    rate_val = (Ce - C0) * k_fit
                else:
                    rate_val = C0 * k_fit

                plot_key = (rxn, analyte, profile_type)
                if plot_key not in st.session_state["kinetics_plotted_keys"]:
                    fig = go.Figure()
                    fig.add_trace(
                        go.Scatter(
                            x=single_df["time"],
                            y=single_df[analyte],
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
                        title=f"{analyte} - Reaction {rxn}",
                        xaxis_title=f"Time ({time_unit})",
                        yaxis_title=selected_measurements,
                        width=400,
                        height=250,
                    )
                    rate_table = pd.DataFrame([{
                        "Reaction": rxn,
                        "Analyte": analyte,
                        "Profile": profile_type,
                        "Rate": rate_val,
                        "C0": C0,
                        "Ce": Ce,
                        "k": k_fit,
                    }])
                    st.session_state["kinetics_plot_history"].append({
                        "reaction": rxn,
                        "analyte": analyte,
                        "profile_type": profile_type,
                        "fig": fig,
                        "rate_table": rate_table,
                        "selected_measurements": selected_measurements,
                        "single_df": single_df,
                        "t_fine": t_fine.tolist(),
                        "y_fit": y_fit.tolist(),
                    })
                    st.session_state["kinetics_plotted_keys"].add(plot_key)

# ---- Display fit plot history grouped by reaction ----
if st.session_state["kinetics_plot_history"]:
    st.divider()
    st.write("### Generated Fit Plots")

    # Group items by reaction, preserving insertion order
    from collections import defaultdict
    groups: dict = defaultdict(list)
    for item in st.session_state["kinetics_plot_history"]:
        groups[item["reaction"]].append(item)

    for rxn, items in groups.items():
        st.write(f"#### Reaction {rxn}")
        # Render up to 2 plots per row
        for i in range(0, len(items), 2):
            row_items = items[i : i + 2]
            cols = st.columns(len(row_items))
            for col, item in zip(cols, row_items):
                with col:
                    st.caption(f"{item['analyte']} ({item['profile_type']})")
                    st.plotly_chart(item["fig"], use_container_width=True)
                    st.dataframe(item["rate_table"], use_container_width=True, hide_index=True)
        st.divider()

    if st.button("Clear all plots", key="clear_plots"):
        st.session_state["kinetics_plot_history"] = []
        st.session_state["kinetics_plotted_keys"] = set()
        st.session_state["kinetics_clear_counter"] += 1
        st.rerun()

st.divider()
st.subheader("Export Report")
try:
    pdf_bytes = generate_report_pdf(
        experiment_setup=st.session_state.get("experiment_setup", {}),
        hplc_file_name=st.session_state.get("hplc_file_name", "-"),
        plot_history=st.session_state.get("kinetics_plot_history", []),
        reaction_plots=reaction_plot_data,
        rate_summaries=rate_summaries,
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
