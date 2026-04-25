from typing import Callable, Optional
import hashlib

import streamlit as st


def _clear_kinetics_plot_state() -> None:
    """Remove persisted fit-plot state so old datasets do not leak into new sessions."""
    st.session_state.pop("kinetics_plot_history", None)
    st.session_state.pop("kinetics_excluded_keys", None)
    st.session_state.pop("kinetics_remove_idx", None)
    st.session_state["kinetics_clear_counter"] = 0


def _maybe_reset_kinetics_on_new_upload(file_bytes: bytes, fp_key: str) -> None:
    """
    Clear kinetics plot artifacts when uploaded file content changes.
    """
    new_fp = hashlib.md5(file_bytes).hexdigest()
    if st.session_state.get(fp_key) != new_fp:
        st.session_state[fp_key] = new_fp
        _clear_kinetics_plot_state()


def experiment_conditions_button(
    template_bytes_fn: Optional[Callable[[], bytes]] = None,
    HPLC: bool = True
):
    with st.container(border=True):
        st.markdown("<div class='upload-card-label'>Experiment Conditions</div>", unsafe_allow_html=True)
        st.caption("Reactions, wells, and time settings")

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
            uploaded_bytes = uploaded.getvalue()
            st.session_state["conditions_file_bytes"] = uploaded_bytes
            st.session_state["conditions_file_name"] = uploaded.name
            _maybe_reset_kinetics_on_new_upload(
                uploaded_bytes, "_conditions_file_upload_fp"
            )
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
            hplc_bytes = hplc_file.read()
            st.session_state["hplc_file_bytes"] = hplc_bytes
            st.session_state["hplc_file_name"] = hplc_file.name
            _maybe_reset_kinetics_on_new_upload(hplc_bytes, "_hplc_file_upload_fp")
            st.success(f"Loaded: {hplc_file.name}")
        elif st.session_state.get("hplc_file_name"):
            st.info(f"Using: {st.session_state['hplc_file_name']}")


def processed_data_button():
    with st.container(border=True):
        st.markdown("<div class='upload-card-label'>Processed Data</div>", unsafe_allow_html=True)
        st.caption(
            "CSV or Excel with Reaction, time, and analyte columns "
            "(see processed-data example on this page)."
        )
        pre_file = st.file_uploader(
            "Upload data: each row should contain reaction, time, and analyte values.",
            type=["csv", "xlsx"],
            key="processed_data_uploader",
            label_visibility="collapsed",
        )
        if pre_file is not None:
            pre_bytes = pre_file.getvalue()
            st.session_state["processed_data_file_bytes"] = pre_bytes
            st.session_state["processed_data_file_name"] = pre_file.name
            _maybe_reset_kinetics_on_new_upload(
                pre_bytes, "_processed_file_upload_fp"
            )
            st.success(f"Loaded: {pre_file.name}")
        elif st.session_state.get("processed_data_file_name"):
            st.info(f"Using: {st.session_state['processed_data_file_name']}")
