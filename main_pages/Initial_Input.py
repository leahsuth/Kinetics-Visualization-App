# pages/initial_input.py

import io
import sys
import hashlib
from pathlib import Path

import pandas as pd
import streamlit as st

from src.page_styling.html import input_page_markdown
from src.page_styling.plate_selector import (
    generate_plate_png,
    render_plate_editor_modal,
)
from src.page_styling.upload_files.file_uploader_buttons import (
    experiment_conditions_button,
    hplc_data_button,
    processed_data_button,
)
from src.parsing.input_page.helpers import (
    clean_list,
    default_plate_color_field,
    parse_excel,
    unique_preserve_order)

from src.parsing.parse_file_type import read_input
from src.parsing.input_page.plate_setup import (
    apply_plate_mode,
    build_well_info,
    finalize_setup,
)
from src.parsing.parsing_cat_loading_conditions import parse_conditions_df
from src.parsing.process_preprocessed_data import (
    normalize_preprocessed_conditions,
    process_preprocessed_data,
    add_loading_data_preprocessed,
)

from src.page_styling.template import excel_template_bytes_HPLC, excel_template_bytes_Processed

st.logo(image='assets/Merck_Logo.png')

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Experiment Setup", layout="wide")

input_page_markdown.setup_header()

st.session_state.setdefault("experiment_setup", {})

source_choice = st.selectbox(
    "Select data source type",
    ("ChemStation", "Processed"),
    index=None,
    help="Choose ChemStation for data directly from ChemStation, or Processed for ready-to-plot data.",
)

input_page_markdown.data_source_help_text()


# ── Step 1: Upload files ────────────────────────────────────────────────────
uploaded = None
if source_choice == "ChemStation":
    input_page_markdown.step_label(1, "Upload Files")

    col_cond, col_hplc = st.columns(2, gap="large")

    with col_cond:
        uploaded = experiment_conditions_button(
            template_bytes_fn=excel_template_bytes_HPLC, HPLC=True)

    with col_hplc:
        hplc_data_button()

if source_choice == "Processed":
    input_page_markdown.preprocessed_file_example()

    input_page_markdown.step_label(1, "Upload Files")

    col_pre, col_meas = st.columns(2, gap="large")

    with col_pre:
        uploaded = experiment_conditions_button(
            template_bytes_fn=excel_template_bytes_Processed, HPLC=False)

    with col_meas:
        processed_data_button()

    input_page_markdown.step_label(2, "Update Measurement Type")
    with st.container(border=True):
        st.markdown("<div class='upload-card-label'>Measurement label</div>", unsafe_allow_html=True)
        st.caption("Used for plot axes (e.g. Concentration, Area %).")
        measurement_type = st.text_input(
            "Measurement type",
            "Concentration",
            label_visibility="collapsed",
            key="preprocessed_measurement_type",
        )
        st.session_state["measurement_type"] = measurement_type

    preprocessed_ready = bool(
        st.session_state.get("processed_data_file_bytes")
        and st.session_state.get("conditions_file_bytes")
    )

    if preprocessed_ready:
        preprocessed_conditions_df = normalize_preprocessed_conditions(
            st.session_state.get("conditions_file_bytes")
        )
        preprocessed_data_df = process_preprocessed_data(st.session_state.get("processed_data_file_bytes"), preprocessed_conditions_df)
        preprocessed_data_df = add_loading_data_preprocessed(preprocessed_data_df, preprocessed_conditions_df)
        st.session_state["preprocessed_data_df"] = preprocessed_data_df

    if not preprocessed_ready:
        st.info(
            "Upload a processed CSV or XLSX file above, then save setup to continue.",
            icon="👇",
        )


# ── Step 2: Configure (only shown after conditions file is uploaded) ─────────

if uploaded is not None:
    try:
        df = read_input(uploaded)
        st.session_state["uploaded_excel_df"] = df
        if df.empty:
            st.error("This uploaded file appears to be empty.")
            st.stop()
        reaction_rows, timepoints, cond_cols = parse_excel(df)
        reaction_rows = apply_plate_mode(reaction_rows)

        # If the uploaded conditions file changes, reset stored plate-editor state.
        # Otherwise, the editor preserves prior wells and can show stale reactions.
        fp_bits = []
        for r in reaction_rows:
            fp_bits.append(
                f"{str(r.get('Reaction', '')).strip()}|{str(r.get('Reaction_Well', '')).strip()}"
            )
        rxn_fp = hashlib.md5("\n".join(fp_bits).encode("utf-8")).hexdigest()
        if st.session_state.get("_excel_reaction_fp") != rxn_fp:
            st.session_state["_excel_reaction_fp"] = rxn_fp
            st.session_state.pop("excel_plate_well_info", None)
            st.session_state.pop("excel_plate_active_well", None)
    except Exception as e:
        st.error(str(e))
        st.stop()

    if source_choice == "ChemStation":
        ready = bool(
            st.session_state.get("hplc_file_bytes")
        )
    elif source_choice == "Processed":
        ready = bool(
            st.session_state.get("processed_data_file_bytes")
        )

    if ready:
        st.info(
            "Both files uploaded. **Review your experiment configuration below and click Save setup** when ready to proceed to the Kinetics page.",
            icon="👇",
        )
    else:
        st.info(
            "Conditions file uploaded. **Review your experiment configuration below, upload your data above, then click Save setup** to proceed.",
            icon="👇",
        )

    input_page_markdown.step_label(2, "Review & Configure")

    with st.expander("Preview reaction table", expanded=False):
        df = pd.DataFrame(reaction_rows)
        df = df.drop(columns=["Notes"])
        st.dataframe(df, use_container_width=True, hide_index=True)

    with st.container(border=True):
        st.markdown("<div class='section-label'>Plate editor</div>", unsafe_allow_html=True)
        if cond_cols:
            st.write(f"Condition columns detected: {', '.join(cond_cols)}")
        
        with st.container(horizontal=True, gap="large", vertical_alignment="center"):
            show_plate = st.toggle(
                "Generate plate map?",
                key="generate_plate_map",
                help="If Yes, open Review & Configure to edit the plate map.",
            )

            # Parsed condition columns; default color is a condition.
            color_choices = ["Reaction"] + cond_cols
            _fp = tuple(cond_cols)
            if st.session_state.get("_excel_cond_cols_fp") != _fp:
                st.session_state["_excel_cond_cols_fp"] = _fp
                st.session_state.pop("excel_color_by", None)

            _default_field = default_plate_color_field(cond_cols)
            if st.session_state.get("excel_color_by") not in color_choices:
                st.session_state["excel_color_by"] = _default_field

            color_by = st.selectbox(
                "Color wells by",
                color_choices,
                key="excel_color_by",
                disabled=not(show_plate),
                width=300
            )

    if show_plate:
        has_wells = any(str(r.get("Reaction_Well", "")).strip() for r in reaction_rows)
        if not has_wells:
            st.session_state.pop("plate_map_png", None)
            st.warning(
                "No plate well data found. Add a **Reaction_Well** column to your "
                "conditions file (e.g. A1, B3) to enable the plate visualization.",
                icon="⚠️",
            )
        else:
            base_info = build_well_info(reaction_rows, cond_cols)
            with st.container(border=True):
                well_info_excel = render_plate_editor_modal(
                    base_info,
                    title="Reaction Plate Map",
                    key_prefix="excel_plate",
                    n_items=len(reaction_rows),
                    color_by=color_by,
                )
                st.session_state["excel_plate_well_info"] = well_info_excel
                plate_png = generate_plate_png(well_info_excel, color_by, len(reaction_rows))
                st.session_state["plate_map_png"] = plate_png
                st.download_button(
                    "Download plate image (.png)",
                    data=plate_png,
                    file_name="plate_map.png",
                    mime="image/png",
                    key="excel_dl_png",
                )
    else:
        st.session_state.pop("plate_map_png", None)
    # ── Step 3: Save & Proceed ─────────────────────────────────────────────
    input_page_markdown.step_label(3, "Save & Proceed")

    if source_choice == "ChemStation":
        save_clicked = st.button("Save setup", type="primary", use_container_width=True, key="excel_save")

        if save_clicked:
            st.session_state["data_source_type"] = source_choice
            well_info = st.session_state.get("excel_plate_well_info") or build_well_info(reaction_rows, cond_cols)
            updated_rows = [well_info.get(r.get("Reaction_Well", ""), dict(r)) for r in reaction_rows]
            for r in updated_rows:
                if not str(r.get("Notes", "")).strip():
                    r["Notes"] = "None"

            st.session_state["experiment_setup"] = finalize_setup(
                "excel", updated_rows, timepoints, cond_cols, well_info, color_by
            )

            rxn_df = pd.DataFrame(updated_rows)
            st.session_state["experiment_setup_df"] = rxn_df

            raw_df = st.session_state.get("uploaded_excel_df")
            if isinstance(raw_df, pd.DataFrame) and not raw_df.empty:
                raw_df_norm = parse_conditions_df(raw_df)
                rxn_df_norm = parse_conditions_df(rxn_df)
                rxn_df_norm = rxn_df_norm.drop(columns=["well"], errors="ignore")
                annotated_df = raw_df_norm.merge(
                    rxn_df_norm, on="Reaction", how="left", suffixes=("", "_rxn")
                )
                st.session_state["cat_loading_df"] = annotated_df
            st.toast("Setup saved! Head to the Kinetics page to visualize your data.")

    elif source_choice == "Processed":
        save_preprocessed = st.button(
            "Save setup",
            type="primary",
            use_container_width=True,
            key="preprocessed_save",
            disabled=not preprocessed_ready,
        )

        if save_preprocessed:
            st.session_state["PREPROCESSED_DATA_DF"] = st.session_state["preprocessed_data_df"]

            # Use the uploaded conditions file (same as ChemStation path) to build the
            # plate map + reaction metadata; otherwise the report plate map is empty/stale.
            st.session_state["data_source_type"] = source_choice
            well_info = st.session_state.get("excel_plate_well_info") or build_well_info(
                reaction_rows, cond_cols
            )
            updated_rows = [
                well_info.get(r.get("Reaction_Well", ""), dict(r)) for r in reaction_rows
            ]
            for r in updated_rows:
                if not str(r.get("Notes", "")).strip():
                    r["Notes"] = "None"

            # Timepoints for processed data come from the processed measurements file.
            processed_tp = unique_preserve_order(
                clean_list(st.session_state["preprocessed_data_df"]["time"].unique())
            )

            st.session_state["experiment_setup"] = finalize_setup(
                "preprocessed",
                updated_rows,
                processed_tp,
                cond_cols,
                well_info,
                color_by,
            )
            st.toast("Setup saved! Head to the Kinetics page to visualize your data.")

# ── Saved setup summary ────────────────────────────────────────────────────

if st.button(
    "📈  Visualize data and initial rates →",
    type="primary",
    width="stretch",
    key="cta_kinetics",
):
    st.switch_page("main_pages/Kinetics.py")

