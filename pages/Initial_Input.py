# pages/initial_input.py
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

from src.page_styling.html import input_page_markdown
from src.page_styling.plate_selector import (
    generate_plate_svg,
    render_plate_editor_modal,
)
from src.page_styling.upload_files.file_uploader_buttons import (
    experiment_conditions_button,
    hplc_data_button,
)
from src.parsing.input_page.helpers import parse_excel
from src.parsing.input_page.plate_setup import (
    apply_plate_mode,
    build_well_info,
    finalize_setup,
)
from src.parsing.parsing_cat_loading_conditions import parse_conditions_df
from src.utils.png_utils import _svg_to_png

st.logo(image='assets/Merck_Logo.png')

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Experiment Setup", layout="wide")

input_page_markdown.input_page_setup()

input_page_markdown.setup_header()

TEMPLATE_COLUMNS = ["Reaction", "Reaction_Well", "Timepoint"]
TEMPLATE_OPTIONAL = ["Condition1", "Condition2"]

st.session_state.setdefault("experiment_setup", {})
st.session_state.setdefault("show_plate_modal", True)
# ── Step 1: Upload files ────────────────────────────────────────────────────

input_page_markdown.step_label(1, "Upload Files")

col_cond, col_hplc = st.columns(2, gap="large")

with col_cond:
    uploaded = experiment_conditions_button()

with col_hplc:
    hplc_data_button()


# ── Step 2: Configure (only shown after conditions file is uploaded) ─────────

if uploaded is not None:
    try:
        df = pd.read_excel(uploaded)
        st.session_state["uploaded_excel_df"] = df
        if df.empty:
            st.error("This Excel file appears to be empty.")
            st.stop()
        reaction_rows, timepoints, cond_cols = parse_excel(df)
        reaction_rows = apply_plate_mode(reaction_rows)
    except Exception as e:
        st.error(str(e))
        st.stop()

    hplc_ready = bool(st.session_state.get("hplc_file_bytes"))
    if hplc_ready:
        st.info(
            "Both files uploaded. **Review your experiment configuration below and click Save setup** when ready to proceed to the Kinetics page.",
            icon="👇",
        )
    else:
        st.info(
            "Conditions file uploaded. **Review your experiment configuration below, upload your HPLC data above, then click Save setup** to proceed.",
            icon="👇",
        )

    input_page_markdown.step_label(2, "Review & Configure")

    with st.container(border=True):
        st.markdown("<div class='section-label'>Plate editor</div>", unsafe_allow_html=True)
        st.session_state["show_plate_modal"] = st.toggle(
            "Enable", value=bool(st.session_state["show_plate_modal"])
        )
        if cond_cols:
            st.caption(f"Condition columns detected: {', '.join(cond_cols)}")

    color_choices = ["Reaction"] + cond_cols
    color_by = st.selectbox(
        "Color wells by",
        options=color_choices,
        index=0,
        key="excel_color_by",
        help="Choose which field drives well colors in the plate map.",
    )

    with st.expander("Preview reaction table", expanded=False):
        st.dataframe(pd.DataFrame(reaction_rows), use_container_width=True, hide_index=True)

    if st.session_state["show_plate_modal"]:
        base_info = build_well_info(reaction_rows, cond_cols)
        with st.container(border=True):
            well_info_excel = render_plate_editor_modal(
                base_info,
                title="Plate Map",
                key_prefix="excel_plate",
                n_items=len(reaction_rows),
                color_by=color_by,
            )
            st.session_state["excel_plate_well_info"] = well_info_excel
            svg = generate_plate_svg(well_info_excel, color_by, len(reaction_rows))
            st.download_button(
                "Download plate image (.png)",
                data=_svg_to_png(svg),
                file_name="plate_map.png",
                mime="image/png",
                use_container_width=True,
                key="excel_dl_png",
            )
    # ── Step 3: Save & Proceed ─────────────────────────────────────────────
    input_page_markdown.step_label(3, "Save & Proceed")

    save_clicked = st.button("Save setup", type="primary", use_container_width=True, key="excel_save")

    if save_clicked:
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
        st.success("Setup saved! Head to the Kinetics page to visualize your data.")
else:
    st.stop()


# ── Saved setup summary ────────────────────────────────────────────────────

setup = st.session_state.get("experiment_setup") or {}

if setup:
    st.divider()
    with st.container(border=True):
        st.markdown("**Saved Setup**")
        a, b, c = st.columns(3)
        a.metric("Reactions", len(setup.get("reaction_rows", [])))
        b.metric("Timepoints", len(setup.get("timepoints", [])))
        hplc_name = st.session_state.get("hplc_file_name", "—")
        c.metric("HPLC File", hplc_name if hplc_name else "—")

        if st.button(
            "📈  Visualize data and initial rates →",
            type="primary",
            use_container_width=True,
            key="cta_kinetics",
        ):
            st.switch_page("pages/Kinetics.py")
