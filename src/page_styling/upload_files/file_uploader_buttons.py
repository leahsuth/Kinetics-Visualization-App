from typing import Callable, Optional

import streamlit as st


def experiment_conditions_button(
    template_bytes_fn: Optional[Callable[[], bytes]] = None,
    HPLC: bool = True
):
    with st.container(border=True):
        st.markdown("<div class='upload-card-label'>Experiment Conditions</div>", unsafe_allow_html=True)
        st.caption("Reactions, wells, and timepoints")

        if template_bytes_fn is not None:
            st.download_button(
                label="Download template",
                data=template_bytes_fn(),
                file_name="experiment_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="experiment_conditions_template_dl",
            )

        with st.popover("Template guide", use_container_width=True):
            if HPLC:
                st.markdown(
                    "| Column | Required? | Notes |\n"
                    "|---|---|---|\n"
                    "| **Timepoint** | Yes | One row per timepoint (**this column is NOT associated with the reaction rows**) |\n"
                    "| **Reaction** | Yes | Unique reaction ID |\n"
                    "| Reaction_Well | Optional | e.g. A1, B3 (used for plate visualization) |\n"
                    "| Any custom name | Optional | Add as many condition columns as needed (e.g. Ligand, Catalyst, Solvent) |"
                )
            else:
                st.markdown(
                    "| Column | Required? | Notes |\n"
                    "|---|---|---|\n"
                    "| **Reaction** | Yes | Unique reaction ID |\n"
                    "| **# of Timepoints** | Yes | Number of timepoints for the reaction |\n"
                    "| Reaction_Well | Optional | e.g. A1, B3 (used for plate visualization) |\n"
                    "| Any custom name | Optional | Add as many condition columns as needed (e.g. Ligand, Catalyst, Solvent) |"
                )

        uploaded = st.file_uploader(
            "Upload conditions (.xlsx, .csv)",
            type=["xlsx", "csv"],
            label_visibility="collapsed",
        )
        if uploaded is not None:
            st.session_state["conditions_file_bytes"] = uploaded.getvalue()
            st.session_state["conditions_file_name"] = uploaded.name
            st.success(f"Loaded: {uploaded.name}")
        elif st.session_state.get("conditions_file_name"):
            st.info(f"Using: {st.session_state['conditions_file_name']}")

        return uploaded


def hplc_data_button():
    with st.container(border=True):
        st.markdown("<div class='upload-card-label'>HPLC Data</div>", unsafe_allow_html=True)
        st.caption("ChemStation Excel export for the Kinetics page.")

        hplc_file = st.file_uploader(
            "Upload HPLC data (.xlsx)",
            type=["xlsx"],
            key="hplc_uploader",
            label_visibility="collapsed",
        )
        if hplc_file is not None:
            st.session_state["hplc_file_bytes"] = hplc_file.read()
            st.session_state["hplc_file_name"] = hplc_file.name
            st.success(f"Loaded: {hplc_file.name}")
        elif st.session_state.get("hplc_file_name"):
            st.info(f"Using: {st.session_state['hplc_file_name']}")


def processed_data_button():
    with st.container(border=True):
        st.markdown("<div class='upload-card-label'>Processed Data</div>", unsafe_allow_html=True)
        st.caption("CSV or Excel with time and analyte columns (see Kinetics page).")
        pre_file = st.file_uploader(
            "Upload data, each row should contain the reaction, timepoint and analyte values.",
            type=["csv", "xlsx"],
            key="processed_data_uploader",
            label_visibility="collapsed",
        )
        if pre_file is not None:
            st.session_state["processed_data_file_bytes"] = pre_file.getvalue()
            st.session_state["processed_data_file_name"] = pre_file.name
            st.success(f"Loaded: {pre_file.name}")
        elif st.session_state.get("processed_data_file_name"):
            st.info(f"Using: {st.session_state['processed_data_file_name']}")
