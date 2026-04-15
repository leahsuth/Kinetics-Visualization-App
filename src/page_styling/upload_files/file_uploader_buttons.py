from typing import Callable, Optional

import streamlit as st


def experiment_conditions_button(
    template_bytes_fn: Optional[Callable[[], bytes]] = None,
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
                width="stretch",
                key="experiment_conditions_template_dl",
            )

        with st.popover("Template guide", width="stretch"):
            st.markdown(
                "| Column | Required? | Notes |\n"
                "|---|---|---|\n"
                "| **Reaction** | Yes | Unique reaction ID |\n"
                "| **Timepoint** | Yes | One row per timepoint |\n"
                "| **Reaction_Well** | Yes | e.g. A1, B3 |\n"
                "| Any custom name | Optional | Add as many condition columns as needed (e.g. Ligand, Catalyst, Solvent) |"
            )

        uploaded = st.file_uploader(
            "Upload conditions (.xlsx)",
            type=["xlsx"],
            label_visibility="collapsed",
        )
        if uploaded is not None:
            st.success(f"Loaded: {uploaded.name}")

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
