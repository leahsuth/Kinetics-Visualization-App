import io
from collections import defaultdict

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.figures.analyte_ratio_graph import (
    build_ratio_df,
    build_ratio_figure,
    build_ratio_long_df,
)
from src.figures.graph_preprocessed_data import graph_preprocessed_data
from src.figures.graph_xl import graph_from_xlsx, update_measurement_label
from src.page_styling.kinetics_page.exporting import export_button_layout
from src.page_styling.kinetics_page.kinetics_styling import rate_table_widget
from src.page_styling.rate_information import build_rate_summary, profile_picker
from src.page_styling.report_generator import generate_report_pdf
from src.parsing.parsing_data import format_download_columns, process_streamlit
from src.parsing.plotting_process import plot_process
from src.parsing.process_preprocessed_data import process_preprocessed_data
from src.regression.rate_calculation import exp_func, kinetics_fit_initial_rate
from src.regression.sync_kinetics_plot_history import sync_kinetics_plot_history

st.logo(image='assets/Merck_Logo.png')
st.set_page_config(
    page_title="Kinetics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.write("# Kinetics Plotter")

experiment_setup_meta = st.session_state.get("experiment_setup", {}) or {}
source_type = experiment_setup_meta.get("source", "excel")
is_preprocessed = source_type == "preprocessed"

if is_preprocessed:
    if "processed_data_file_bytes" not in st.session_state:
        st.info("Please upload a preprocessed file on the Experiment Setup page to begin.")
        st.stop()
else:
    if "hplc_file_bytes" not in st.session_state:
        st.info("Please upload an HPLC file on the Experiment Setup page to begin.")
        st.stop()
    if "cat_loading_df" not in st.session_state:
        st.info("Please complete and save the Experiment Setup before viewing kinetics.")
        st.stop()

with st.spinner("Loading data..."):
    if is_preprocessed:
        final_df = st.session_state["PREPROCESSED_DATA_DF"]
        st.session_state["first_line"] = "NEED TO ADD FIRST LINE, OR THIS MAY NOT EXIST?"
    else:
        uploaded_file = io.BytesIO(st.session_state["hplc_file_bytes"])
        uploaded_file.name = st.session_state.get("hplc_file_name", "hplc_data.xlsx")
        experiment_setup = st.session_state.get("cat_loading_df")
        try:
            final_df, df_after_add_loading, first_line = process_streamlit(
                experiment_setup, uploaded_file
            )
            st.session_state["first_line"] = first_line
        except Exception as e:
            st.error(
                "Unable to parse the uploaded HPLC file. "
                "Please confirm it is a ChemStation export (with a 'Peak RT' header row), "
                "then re-upload and try again."
            )
            st.caption(str(e))
            st.stop()

# Collect one entry per selected reaction for the PDF report
reaction_plot_data = []
analyte_ratio_plot_data = []

# ----Plotting----------------------------------------
if is_preprocessed:
    st.success("Loaded processed data file.")

    reactions = final_df["Reaction"].dropna().astype(str).unique().tolist()
    selected_reactions = st.multiselect(
        "Select reactions to plot",
        reactions,
    )
    if not selected_reactions:
        st.warning("Please select at least one reaction.")
        st.stop()

    df_plot = final_df[final_df["Reaction"].astype(str).isin(selected_reactions)]

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

    analytes = [
        c
        for c in df_plot.columns
        if c not in ("time", "Reaction", "Sample Name")
    ]
    analytes = sorted(analytes)

    selected_analytes = st.multiselect(
        "Select analytes to plot",
        analytes,
        default=analytes if len(analytes) <= 8 else analytes[:5],
    )
    if not selected_analytes:
        st.warning("Please select at least one analyte.")
        st.stop()

    _chart_cols = ["time", "Reaction"] + [
        c for c in selected_analytes if c in df_plot.columns
    ]
    df_preproc_plot = df_plot[_chart_cols]

    color_options = ["Reaction", "Analyte"]
    default_color_by = st.session_state.get("_kinetics_color_by", "Analyte")
    if default_color_by not in color_options:
        default_color_by = color_options[0] if color_options else "Reaction"

    if is_preprocessed:
        default_color_by = "Analyte"

    color_by = st.radio(
        "Color by:",
        color_options or ["Reaction"],
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

    colorblind_shapes = st.toggle(
        "Colorblind-friendly: distinct marker shapes",
        key="_kinetics_colorblind_shapes",
    )

    multi_plot_choice = st.radio(
        "Generate a plot for every reaction?",
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

    if reactions_for_plots:
        for i in range(0, len(reactions_for_plots), 2):
            row_reactions = reactions_for_plots[i: i + 2]
            cols = st.columns(len(row_reactions))
            for col, rxn in zip(cols, row_reactions):
                with col:
                    df_rxn = df_preproc_plot[
                        df_preproc_plot["Reaction"].astype(str) == str(rxn)
                    ]
                    if not df_rxn.empty:
                        graph_preprocessed_data(
                            df=df_rxn,
                            color_select=color_by,
                            chart_type=chart_type,
                            time_unit=time_unit,
                            title_suffix=f"Reaction {rxn}",
                            colorblind_shapes=colorblind_shapes,
                        )

    remaining_reactions = [r for r in selected_reactions if r not in reactions_for_plots]
    if remaining_reactions:
        df_remaining = df_preproc_plot[
            df_preproc_plot["Reaction"].astype(str).isin(remaining_reactions)
        ]
        graph_preprocessed_data(
            df=df_remaining,
            color_select=color_by,
            chart_type=chart_type,
            time_unit=time_unit,
            colorblind_shapes=colorblind_shapes,
        )

    ratio_df = pd.DataFrame()
    ratio_numerator = ""
    ratio_denominator = ""
    generate_ratio_plot = st.radio(
        "Generate analyte ratio plot?",
        ["No", "Yes"],
        horizontal=True,
        key="generate_ratio_plot_preprocessed",
    )
    if generate_ratio_plot == "Yes":
        ratio_chart_type = st.radio(
            "Chart type",
            ["Scatter", "Line"],
            horizontal=True,
            key="ratio_chart_type_preprocessed",
        )
        num_col, denom_col = st.columns(2)
        with num_col:
            ratio_numerator = st.selectbox(
                "Numerator",
                options=analytes,
                key="ratio_numerator_preprocessed",
            )
        with denom_col:
            denominator_options = [a for a in analytes if a != ratio_numerator]
            ratio_denominator = st.selectbox(
                "Denominator",
                options=denominator_options if denominator_options else analytes,
                key="ratio_denominator_preprocessed",
            )

        numerator, denominator = ratio_numerator, ratio_denominator
        ratio_label = f"{numerator}/{denominator}"
        ratio_df = build_ratio_df(
            df=df_preproc_plot,
            reaction_col="Reaction",
            numerator=numerator,
            denominator=denominator,
        )
        if ratio_df.empty:
            st.warning("No data available for the ratio plot.")
        elif reactions_for_plots:
            for i in range(0, len(reactions_for_plots), 2):
                row_reactions = reactions_for_plots[i: i + 2]
                cols = st.columns(len(row_reactions))
                for col, rxn in zip(cols, row_reactions):
                    with col:
                        df_ratio_rxn = ratio_df[
                            ratio_df["Reaction"].astype(str) == str(rxn)
                        ]
                        fig, err = build_ratio_figure(
                            df=df_ratio_rxn,
                            reaction_col="Reaction",
                            chart_type=ratio_chart_type,
                            time_unit=time_unit,
                            title_suffix=f"Reaction {rxn}",
                            ratio_label=ratio_label,
                        )
                        if err:
                            st.warning(err)
                        else:
                            st.plotly_chart(fig, use_container_width=True)
        else:
            ratio_remaining = ratio_df[
                ratio_df["Reaction"].astype(str).isin(remaining_reactions)
            ]
            fig, err = build_ratio_figure(
                df=ratio_remaining,
                reaction_col="Reaction",
                chart_type=ratio_chart_type,
                time_unit=time_unit,
                ratio_label=ratio_label,
            )
            if err:
                st.warning(err)
            else:
                st.plotly_chart(fig, use_container_width=True)

        # Collect analyte-ratio entries for PDF report
        for rxn in selected_reactions:
            df_ratio_rxn = ratio_df[ratio_df["Reaction"].astype(str) == str(rxn)]
            if df_ratio_rxn.empty:
                continue
            analyte_ratio_plot_data.append({
                "reaction": rxn,
                "df": df_ratio_rxn,
                "numerator": numerator,
                "denominator": denominator,
                "color_by": "Reaction",
                "title_text": f"{ratio_label} vs. Time for Reaction {rxn}",
                "x_label": f"Time ({time_unit})",
                "y_label": ratio_label,
            })

    # Collect one entry per selected reaction for the PDF report
    for rxn in selected_reactions:
        df_rxn = df_preproc_plot[df_preproc_plot["Reaction"].astype(str) == str(rxn)]
        if df_rxn.empty:
            continue
        value_cols = [a for a in selected_analytes if a in df_rxn.columns]
        if not value_cols:
            continue
        long_rxn = (
            df_rxn.melt(
                id_vars=["time", "Reaction"],
                value_vars=value_cols,
                var_name="reactant",
                value_name="value",
            )
            .dropna(subset=["time", "value"])
            .copy()
        )
        if long_rxn.empty:
            continue
        color_by_pdf = "reactant" if color_by == "Analyte" else color_by
        measurement_type = st.session_state.get("measurement_type", "Concentration")
        reaction_plot_data.append({
            "reaction": rxn,
            "df": long_rxn,
            "select_meas": "value",
            "color_by": color_by_pdf,
            "chart_type": chart_type,
            "title_text": f"{measurement_type} vs. Time for Reaction {rxn}",
            "x_label": f"Time ({time_unit})",
            "y_label": measurement_type,
        })

else:
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

    # INFO: peak_area vs AP is being set here
    df_plot, selected_measurements = plot_process(df_plot, selected_reactions, selected_analytes)

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
        "Generate a plot for every reaction?",
        ["No", "Yes"],
        index=1,
        horizontal=True,
    )

    colorblind_shapes = st.toggle(
        "Colorblind-friendly: distinct marker shapes",
        key="_kinetics_colorblind_shapes",
    )

    reactions_for_plots: list[str] = []
    if multi_plot_choice == "Yes":
        reactions_for_plots = st.multiselect(
            "Reactions to display as separate plots.",
            options=selected_reactions,
            default=selected_reactions,
        )

    if reactions_for_plots:
        for i in range(0, len(reactions_for_plots), 2):
            row_reactions = reactions_for_plots[i: i + 2]
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
                            colorblind_shapes=colorblind_shapes,
                        )
                        st.plotly_chart(fig, width="stretch")

    remaining_reactions = [r for r in selected_reactions if r not in reactions_for_plots]
    if remaining_reactions:
        df_remaining = df_plot[df_plot["reaction"].astype(str).isin(remaining_reactions)]
        fig = graph_from_xlsx(
            df=df_remaining,
            select_meas=selected_measurements,
            color_select=color_by,
            chart_type=chart_type,
            time_unit=time_unit,
            colorblind_shapes=colorblind_shapes,
        )
        st.plotly_chart(fig, width="stretch")

    # ----Analyte Ratio Plot----------------------------------------
    ratio_df = pd.DataFrame()
    ratio_numerator = ""
    ratio_denominator = ""
    generate_ratio_plot = st.radio(
        "Generate analyte ratio plot?",
        ["No", "Yes"],
        horizontal=True,
        key="generate_ratio_plot_hplc",
    )
    if generate_ratio_plot == "Yes":
        ratio_chart_type = st.radio(
            "Chart type",
            ["Scatter", "Line"],
            horizontal=True,
            key="ratio_chart_type_hplc",
        )
        num_col, denom_col = st.columns(2)
        with num_col:
            ratio_numerator = st.selectbox(
                "Numerator",
                options=analytes,
                key="ratio_numerator_hplc",
            )
        with denom_col:
            denominator_options = [a for a in analytes if a != ratio_numerator]
            ratio_denominator = st.selectbox(
                "Denominator",
                options=denominator_options if denominator_options else analytes,
                key="ratio_denominator_hplc",
            )

        numerator, denominator = ratio_numerator, ratio_denominator
        ratio_label = f"{numerator}/{denominator}"
        ratio_analytes = [numerator, denominator]
        ratio_df = build_ratio_long_df(
            df=df_plot,
            reaction_col="reaction",
            reactant_col="reactant",
            value_col=selected_measurements,
            ratio_analytes=ratio_analytes,
            numerator=numerator,
            denominator=denominator,
        )
        if ratio_df.empty:
            st.warning("No data available for the ratio plot.")
        elif reactions_for_plots:
            for i in range(0, len(reactions_for_plots), 2):
                row_reactions = reactions_for_plots[i: i + 2]
                cols = st.columns(len(row_reactions))
                for col, rxn in zip(cols, row_reactions):
                    with col:
                        df_ratio_rxn = ratio_df[
                            ratio_df["reaction"].astype(str) == str(rxn)
                        ]
                        fig, err = build_ratio_figure(
                            df=df_ratio_rxn,
                            reaction_col="reaction",
                            chart_type=ratio_chart_type,
                            time_unit=time_unit,
                            title_suffix=f"Reaction {rxn}",
                            ratio_label=ratio_label,
                        )
                        if err:
                            st.warning(err)
                        else:
                            st.plotly_chart(fig, use_container_width=True)
        else:
            ratio_remaining = ratio_df[
                ratio_df["reaction"].astype(str).isin(remaining_reactions)
            ]
            fig, err = build_ratio_figure(
                df=ratio_remaining,
                reaction_col="reaction",
                chart_type=ratio_chart_type,
                time_unit=time_unit,
                ratio_label=ratio_label,
            )
            if err:
                st.warning(err)
            else:
                st.plotly_chart(fig, use_container_width=True)

        # Collect analyte-ratio entries for PDF report
        for rxn in selected_reactions:
            df_ratio_rxn = ratio_df[ratio_df["reaction"].astype(str) == str(rxn)]
            if df_ratio_rxn.empty:
                continue
            analyte_ratio_plot_data.append({
                "reaction": rxn,
                "df": df_ratio_rxn,
                "numerator": numerator,
                "denominator": denominator,
                "color_by": "reaction",
                "title_text": f"{ratio_label} vs. Time for Reaction {rxn}",
                "x_label": f"Time ({time_unit})",
                "y_label": ratio_label,
            })

    first_line = st.session_state["first_line"]
    st.caption(first_line)

    # Collect one entry per selected reaction for the PDF report
    for rxn in selected_reactions:
        df_rxn = df_plot[df_plot["reaction"].astype(str) == str(rxn)]
        if not df_rxn.empty:
            pretty_meas = update_measurement_label(selected_measurements)
            reaction_plot_data.append({
                "reaction": rxn,
                "df": df_rxn,
                "select_meas": selected_measurements,
                "color_by": color_by,
                "title_text": f"{pretty_meas} vs. Time for Reaction {rxn}",
                "x_label": f"Time ({time_unit})",
                "y_label": pretty_meas,
            })

rate_summaries = []

# ----Initial Rate----------------------------------------
st.divider()
st.write("# Initial Rate Calculations")

k_constant = st.number_input(
    "Rate constant (k)", value=0.1, min_value=1e-10, format="%0.2f", key="k_rate"
)

if "kinetics_plot_history" not in st.session_state:
    st.session_state["kinetics_plot_history"] = []
if "kinetics_excluded_keys" not in st.session_state:
    st.session_state["kinetics_excluded_keys"] = set()
if "kinetics_clear_counter" not in st.session_state:
    st.session_state["kinetics_clear_counter"] = 0


# add y_measure_label
if is_preprocessed:
    y_measure_label = st.session_state.get("measurement_type", "Concentration")
else:
    y_measure_label = selected_measurements

# Compute pivot tables once per reaction and reuse for both summary and fit plots
df_rate_by_rxn: dict = {}
for rxn in selected_reactions:
    if is_preprocessed:
        df_rxn = df_preproc_plot[df_preproc_plot["Reaction"].astype(str) == str(rxn)]
        if df_rxn.empty:
            continue
        value_cols = [a for a in selected_analytes if a in df_rxn.columns]
        if not value_cols:
            continue
        long_rxn = (
            df_rxn.melt(
                id_vars=["time", "Reaction"],
                value_vars=value_cols,
                var_name="reactant",
                value_name="value",
            )
            .dropna(subset=["time", "value"])
            .copy()
        )
        long_rxn["time"] = pd.to_numeric(long_rxn["time"], errors="coerce")
        long_rxn["value"] = pd.to_numeric(long_rxn["value"], errors="coerce")
        long_rxn = long_rxn.dropna(subset=["time", "value"])
        if long_rxn.empty:
            continue
        df_rate_by_rxn[rxn] = (
            long_rxn.pivot_table(
                index="time", columns="reactant", values="value", aggfunc="mean"
            )
            .reset_index()
            .sort_values("time")
        )
    else:
        df_rxn = df_plot[df_plot["reaction"].astype(str) == str(rxn)]
        if not df_rxn.empty:
            df_rate_by_rxn[rxn] = (
                df_rxn.pivot_table(
                    index="time", columns="reactant", values="peak_ap", aggfunc="mean"
                )
                .reset_index()
                .sort_values("time")
            )

# ---- Rate Summary ----
st.write("### Rate Summary")
for rxn in selected_reactions:
    df_pivot = df_rate_by_rxn.get(rxn)
    if df_pivot is None:
        continue
    rxn_analytes = [a for a in selected_analytes if a in df_pivot.columns]
    if not rxn_analytes:
        continue
    summary = build_rate_summary(df_pivot, rxn_analytes, k_constant)
    st.write(f"**Reaction {rxn}**")
    st.dataframe(summary, width="stretch")
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
    chosen_rxn_analytes: set = set()

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
        chosen_rxn_analytes.update((rxn, a) for a in chosen_analytes)
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
            out = kinetics_fit_initial_rate(
                single_df, analyte, k_constant, profile_type, C0_init, Ce_init)
            if out is not None:
                rate_val, C0, Ce, k_fit = out
                t_fine = np.linspace(
                    float(single_df["time"].min()),
                    float(single_df["time"].max()),
                    100,
                )
                y_fit = exp_func(C0, Ce, k_fit, t_fine, profile_type)

                plot_key = (rxn, analyte, profile_type)
                already_exists = any(
                    h["reaction"] == rxn and h["analyte"] == analyte
                    and h["profile_type"] == profile_type
                    for h in st.session_state["kinetics_plot_history"]
                )
                is_excluded = plot_key in st.session_state["kinetics_excluded_keys"]
                if not already_exists and not is_excluded:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=single_df["time"],
                        y=single_df[analyte],
                        mode="markers",
                        name="data",
                    ))
                    fig.add_trace(go.Scatter(
                        x=t_fine,
                        y=y_fit,
                        mode="lines",
                        name="fitted curve",
                        line=dict(color="#E53935", width=2),
                    ))
                    fig.update_layout(
                        xaxis_title=f"Time ({time_unit})",
                        yaxis_title=y_measure_label,
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
                        "selected_measurements": y_measure_label,
                        "single_df": single_df,
                        "t_fine": t_fine.tolist(),
                        "y_fit": y_fit.tolist(),
                    })

    # Remove history plots for (rxn, analyte) pairs the user has deselected
    st.session_state["kinetics_plot_history"] = [
        h for h in st.session_state["kinetics_plot_history"]
        if (h["reaction"], h["analyte"]) in chosen_rxn_analytes
    ]

sync_kinetics_plot_history(
    st.session_state["kinetics_plot_history"],
    k_constant,
    time_unit,
    y_measure_label,
)

# ---- Display fit plot history ----
if "kinetics_remove_idx" not in st.session_state:
    st.session_state["kinetics_remove_idx"] = None

if st.session_state["kinetics_remove_idx"] is not None:
    idx_to_remove = st.session_state["kinetics_remove_idx"]
    st.session_state["kinetics_remove_idx"] = None
    history = st.session_state["kinetics_plot_history"]
    if 0 <= idx_to_remove < len(history):
        removed = history.pop(idx_to_remove)
        st.session_state["kinetics_excluded_keys"].add(
            (removed["reaction"], removed["analyte"], removed["profile_type"])
        )
    st.rerun()

if st.session_state["kinetics_plot_history"]:
    st.divider()
    st.subheader("Export Report")
    try:
        pdf_bytes = generate_report_pdf(
            experiment_setup=st.session_state.get("experiment_setup", {}),
            hplc_file_name=st.session_state.get("hplc_file_name", "-"),
            plot_history=st.session_state.get("kinetics_plot_history", []),
            reaction_plots=reaction_plot_data,
            analyte_ratio_plots=analyte_ratio_plot_data,
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

    with st.container():
        st.markdown("#### Clear plots to reset plotting settings and start fresh.")
        if st.button("Clear all plots", key="clear_plots", type="tertiary"):
            st.session_state["kinetics_plot_history"] = []
            st.session_state["kinetics_excluded_keys"] = set()
            st.session_state["kinetics_clear_counter"] += 1
            st.rerun()

    analyte_groups: dict = defaultdict(list)
    for idx, item in enumerate(st.session_state["kinetics_plot_history"]):
        analyte_groups[item["analyte"]].append((idx, item))

    for analyte, indexed_items in analyte_groups.items():
        for i in range(0, len(indexed_items), 2):
            row = indexed_items[i : i + 2]
            cols = st.columns(len(row))
            for col, (idx, item) in zip(cols, row):
                with col:
                    rt = item["rate_table"].iloc[0]
                    caption = f"Reaction {item['reaction']}-{analyte}"
                    rt_rate = rt['Rate']
                    rt_C0 = rt['C0']
                    rt_Ce = rt['Ce']
                    rt_k = rt['k']
                    mode = item['profile_type']
                    _, c1 = st.columns([5,1])
                    clear_button = c1.button("X", key=f"del_plot_{idx}_{col}", type='tertiary', help="Remove this plot")
                    st.plotly_chart(item["fig"], key=f"plot_{idx}_{col}", width="stretch")
                    if clear_button:
                        st.session_state["kinetics_remove_idx"] = idx
                        st.rerun()
                    rate_table_widget(caption, rt_rate, rt_C0, rt_Ce, rt_k, mode)
        st.divider()

if is_preprocessed:
    export_button_layout(df_preproc_plot, is_preprocessed, reaction_plot_data, rate_summaries)
else:
    export_button_layout(df_after_add_loading, is_preprocessed, reaction_plot_data, rate_summaries)
