import io
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from src.parsing.parsing_data import process_streamlit
from src.parsing.process_preprocessed_data import process_preprocessed_data
from src.page_styling.rate_information import rate_information, profile_picker
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

rate_reaction = "-"
rate = None
rate_params: dict = {}

# ----Initial Rate----------------------------------------
# ChemStation workflow stores setup as source "excel", not session "ChemStation".
if not is_preprocessed:
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
    df_rate = df_rate.sort_values(by="time")

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
        single_df = df_rate[["time", choose_analyte]].copy()
        single_df["time"] = pd.to_numeric(single_df["time"], errors="coerce")
        single_df[choose_analyte] = pd.to_numeric(single_df[choose_analyte],
                                                errors="coerce")
        single_df = single_df.dropna(subset=["time", choose_analyte]).\
            sort_values("time").reset_index(drop=True)

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
                t_min = float(single_df["time"].min())
                t_max = float(single_df["time"].max())
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
                        x=single_df["time"],
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

    st.divider()
    st.subheader("Download data file")
    st.caption(
        "HPLC data file after **add_loading_data_info** (experiment conditions, reaction, time merged in)."
    )
    _hplc_name = st.session_state.get("hplc_file_name") or "hplc_data"
    _stem = _hplc_name.rsplit(".", 1)[0] if "." in _hplc_name else _hplc_name
    _merged_csv = df_after_add_loading.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download processed data (.csv)",
        data=_merged_csv,
        file_name=f"{_stem}_processed.csv",
        mime="text/csv",
        use_container_width=True,
        type="primary",
        key="chemstation_download_processed_csv",
    )
