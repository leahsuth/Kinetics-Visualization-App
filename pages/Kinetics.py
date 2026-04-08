import io
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from src.parsing.parsing_data import process_streamlit, format_download_columns
from src.parsing.process_preprocessed_data import process_preprocessed_data
from src.page_styling.rate_information import profile_picker
from src.figures.graph_xl import graph_from_xlsx
from src.figures.graph_preprocessed_data import graph_preprocessed_data
from src.parsing.plotting_process import plot_process
from src.regression.rate_calculation import rate_calculation, fit_kinetics_and_return_params, exp_func
from src.page_styling.report_generator import generate_report_pdf

st.logo(image='assets/Merck_Logo.png')
st.write("# Kinetics Plotter")

# Make all st.button(type="primary") red (does not affect st.download_button)
st.markdown(
    """
    <style>
    div[data-testid="stButton"] button[kind="primary"] {
        background-color: #c62828 !important;
        border-color: #c62828 !important;
        color: white !important;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        background-color: #b71c1c !important;
        border-color: #b71c1c !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


experiment_setup_meta = st.session_state.get("experiment_setup", {}) or {}
source_type = experiment_setup_meta.get("source", "excel")
is_preprocessed = source_type == "preprocessed"

if is_preprocessed:
    if "preprocessed_file_bytes" not in st.session_state:
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
        final_df, df_after_add_loading, first_line = process_streamlit(
            experiment_setup, uploaded_file
        )
        st.session_state["first_line"] = first_line

# ----Plotting----------------------------------------
if is_preprocessed:
    st.success("Loaded preprocessed file.")

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
    default_color_by = st.session_state.get("_kinetics_color_by", "Reaction")
    if default_color_by not in color_options:
        default_color_by = color_options[0] if color_options else "Reaction"

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
        )

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
                        )
                        st.plotly_chart(fig, use_container_width=True)

    remaining_reactions = [r for r in selected_reactions if r not in reactions_for_plots]
    if remaining_reactions:
        df_remaining = df_plot[df_plot["reaction"].astype(str).isin(remaining_reactions)]
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

    # Collect one entry per selected reaction for the PDF report
    reaction_plot_data = []
    for rxn in selected_reactions:
        df_rxn = df_plot[df_plot["reaction"].astype(str) == str(rxn)]
        if not df_rxn.empty:
            reaction_plot_data.append({
                "reaction": rxn,
                "df": df_rxn,
                "select_meas": selected_measurements,
                "color_by": color_by,
            })

rate_summaries = []

# ----Initial Rate----------------------------------------
if not is_preprocessed:
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

        # Remove history plots for (rxn, analyte) pairs the user has deselected
        st.session_state["kinetics_plot_history"] = [
            h for h in st.session_state["kinetics_plot_history"]
            if (h["reaction"], h["analyte"]) in chosen_rxn_analytes
        ]

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
        st.write("### Generated Fit Plots")

        hdr_col, btn_col = st.columns([3, 1])
        with hdr_col:
            st.caption("Clear plots to reset plotting settings and start fresh.")
        with btn_col:
            if st.button("Clear all plots", key="clear_plots", type="primary",
                         use_container_width=True):
                st.session_state["kinetics_plot_history"] = []
                st.session_state["kinetics_excluded_keys"] = set()
                st.session_state["kinetics_clear_counter"] += 1
                st.rerun()

        from collections import defaultdict
        analyte_groups: dict = defaultdict(list)
        for idx, item in enumerate(st.session_state["kinetics_plot_history"]):
            analyte_groups[item["analyte"]].append((idx, item))

        for analyte, indexed_items in analyte_groups.items():
            st.write(f"#### {analyte}")
            for i in range(0, len(indexed_items), 2):
                row = indexed_items[i : i + 2]
                cols = st.columns(len(row))
                for col, (idx, item) in zip(cols, row):
                    with col:
                        hdr_left, hdr_right = st.columns([5, 1])
                        with hdr_left:
                            st.caption(f"Reaction {item['reaction']} ({item['profile_type']})")
                        with hdr_right:
                            if st.button("✕", key=f"del_plot_{idx}", help="Remove this plot"):
                                st.session_state["kinetics_remove_idx"] = idx
                                st.rerun()
                        st.plotly_chart(item["fig"], use_container_width=True)
                        rt = item["rate_table"].iloc[0]
                        st.markdown(
                            f"<div style='border: 2.5px solid #555; border-radius: 6px; "
                            f"padding: 6px 10px; display: inline-block; font-size: 0.82em; "
                            f"line-height: 1.8;'>"
                            f"<b>Rate:</b> {rt['Rate']:.4f}<br>"
                            f"<b>C\u2080:</b> {rt['C0']:.4f} &nbsp; "
                            f"<b>C\u2091:</b> {rt['Ce']:.4f} &nbsp; "
                            f"<b>k:</b> {rt['k']:.4f}"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
            st.divider()

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

    st.divider()
    st.subheader("Download Processed Data File")
    st.caption(
        "HPLC data file, includes information from the initial input file (i.e., reaction number, wells, timepoints)."
    )
    _hplc_name = st.session_state.get("hplc_file_name") or "hplc_data"
    _stem = _hplc_name.rsplit(".", 1)[0] if "." in _hplc_name else _hplc_name
    download_df = format_download_columns(df_after_add_loading)
    _merged_csv = download_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download processed data (.csv)",
        data=_merged_csv,
        file_name=f"{_stem}_processed.csv",
        mime="text/csv",
        use_container_width=True,
        type="primary",
        key="chemstation_download_processed_csv",
    )
