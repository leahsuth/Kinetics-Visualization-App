# pages/initial_input.py
import re
import io
import sys
from pathlib import Path
from typing import Optional, Dict, List

import streamlit as st
import pandas as pd
from src.parsing import parsing_initial_input

st.logo(image='assets/Merck_Logo.png')

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.page_styling.plate_selector import render_plate_editor_modal, generate_plate_svg  # noqa: E402

try:
    import cairosvg
    def _svg_to_png(svg_str: str) -> bytes:
        return cairosvg.svg2png(bytestring=svg_str.encode())
except Exception:
    _svg_to_png = None


st.set_page_config(page_title="Experiment Setup", layout="wide")

st.markdown(
    """
    <style>
      .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1200px; }
      h1 { margin-bottom: 0.15rem; }
      div[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 14px; }
      .section-label {
        font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em;
        text-transform: uppercase; color: rgba(49,51,63,.45); margin-bottom: 4px;
      }
      .info-pill {
        display: inline-block; background: #eef4ff; color: #1a56db;
        border-radius: 20px; padding: 3px 10px; font-size: 0.8rem; font-weight: 600;
      }
      .step-row {
        display: flex; align-items: center; gap: 10px; margin: 1.2rem 0 0.4rem 0;
      }
      .step-badge {
        display: inline-flex; align-items: center; justify-content: center;
        width: 28px; height: 28px; border-radius: 50%;
        background: #1a56db; color: white;
        font-size: 0.82rem; font-weight: 700; flex-shrink: 0;
      }
      .step-title {
        font-size: 1.05rem; font-weight: 700; color: #1f2937; margin: 0;
      }
      .upload-card-label {
        font-size: 1rem; font-weight: 700; margin-bottom: 2px;
      }
      div[data-testid="stButton"]:has(button[key="cta_kinetics"]) button {
        padding: 18px 24px; font-size: 1.2rem; font-weight: 700;
        border-radius: 10px; letter-spacing: 0.01em;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Experiment Setup")
st.caption("Upload your conditions and HPLC files, configure reactions, then save to proceed.")

TEMPLATE_COLUMNS = ["Reaction", "Plate_Well", "Timepoint"]
TEMPLATE_OPTIONAL = ["Ligand", "Catalyst"]


def init_state() -> None:
    st.session_state.setdefault("experiment_setup", {})
    st.session_state.setdefault("show_plate_modal", True)
    st.session_state.setdefault("multi_injections", False)
    st.session_state.setdefault("num_injections", 1)


init_state()


# ── helpers ────────────────────────────────────────────────────────────────


def clean_list(vals: List[str]) -> List[str]:
    return [str(v).strip() for v in vals if str(v).strip() and str(v).strip().lower() != "nan"]


def unique_preserve_order(items: List[str]) -> List[str]:
    seen: set = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def find_col_contains(columns, *needles: str) -> Optional[str]:
    cols = [str(c).strip() for c in columns]
    low = [c.lower() for c in cols]
    needles = [n.strip().lower() for n in needles if n and n.strip()]
    for n in needles:
        for i, c in enumerate(low):
            if c == n:
                return cols[i]
    for i, c in enumerate(low):
        for n in needles:
            if n in c:
                return cols[i]
    return None


def normalize_well(well: str) -> Optional[str]:
    if well is None:
        return None
    w = str(well).strip().upper()
    if not w or w.lower() == "nan":
        return None
    m = re.match(r"^([A-H])\s*0*([1-9]|1[0-2])$", w)
    if not m:
        return None
    return f"{m.group(1)}{int(m.group(2))}"


def parse_excel(df: pd.DataFrame) -> tuple[List[dict], List[str], List[str]]:
    df = normalize_headers(df)
    reaction_col = find_col_contains(df.columns, "reaction", "rxn")
    time_col = find_col_contains(df.columns, "timepoint", "time point", "timepoints", "tp")
    well_col = find_col_contains(df.columns, "plate_well", "plate well", "well")
    role_col = find_col_contains(df.columns, "role", "type")

    if reaction_col is None:
        raise ValueError('Missing required column containing "reaction".')
    if time_col is None:
        raise ValueError('Missing required column containing "timepoint".')

    timepoints = unique_preserve_order(clean_list(df[time_col].tolist()))
    if not timepoints:
        raise ValueError("No usable timepoints found.")

    excluded = {c for c in [reaction_col, time_col, well_col, role_col] if c}
    cond_cols = [
        c for c in df.columns
        if c not in excluded
        and df[c].astype(str).str.strip().replace("nan", "").str.len().gt(0).any()
    ]
    rxn_series = df[reaction_col].astype(str).str.strip()
    df_rxn = df[rxn_series.astype(bool) & (rxn_series.str.lower() != "nan")].copy()
    rxn_ids = unique_preserve_order(clean_list(df_rxn[reaction_col].tolist()))
    rxn_meta = df_rxn.drop_duplicates(subset=[reaction_col], keep="first").reset_index(drop=True)

    rows = []
    for i, rxn in enumerate(rxn_ids):
        r: dict = {"Reaction": rxn, "Plate_Well": "", "Notes": "None"}
        if well_col:
            r["Plate_Well"] = str(rxn_meta.loc[i, well_col]).strip()
        for c in cond_cols:
            r[c] = str(rxn_meta.loc[i, c]).strip()
        # Notes always starts as "None" when empty
        if not str(r.get("Notes", "")).strip():
            r["Notes"] = "None"
        # Role: read from file if present, default to "Reactant"
        if role_col:
            val = str(rxn_meta.loc[i, role_col]).strip()
            r["Role"] = val if val in ("Reactant", "Product") else "Reactant"
        else:
            r["Role"] = "Reactant"
        rows.append(r)

    return rows, timepoints, cond_cols


def build_well_info(reaction_rows: List[dict], cond_cols: List[str]) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for r in reaction_rows:
        well = str(r.get("Plate_Well", "")).strip()
        if not well:
            continue
        d = dict(r)
        for c in cond_cols:
            d[c] = str(d.get(c, "") or "").strip()
        out[well] = d
    return out


def apply_plate_mode(reaction_rows: List[dict]) -> List[dict]:
    rows = [dict(r) for r in reaction_rows]
    for r in rows:
        r["Plate_Well"] = normalize_well(r.get("Plate_Well", "")) or str(r.get("Plate_Well", "")).strip()
    return rows


def finalize_setup(
    source: str, reaction_rows: List[dict], timepoints: List[str],
    cond_cols: List[str], well_info: Dict[str, dict], color_by: str = "Reaction"
) -> dict:
    reactions = []
    for r in reaction_rows:
        rxn = str(r.get("Reaction", "")).strip()
        well = str(r.get("Plate_Well", "")).strip()
        cond_bits = [f"{c}:{str(r.get(c,'') or '').strip()}" for c in cond_cols if str(r.get(c, "") or "").strip()]
        suffix = " | " + "  ".join(cond_bits) if cond_bits else ""
        reactions.append(f"{rxn} | {well}{suffix}")
    return {
        "source": source,
        "num_injections": int(st.session_state["num_injections"]),
        "timepoints": timepoints,
        "condition_columns": cond_cols,
        "reaction_rows": reaction_rows,
        "reactions": reactions,
        "well_info": well_info,
        "color_by": color_by,
        "reaction_roles": {r["Reaction"]: r.get("Role", "Reactant") for r in reaction_rows},
    }


# ── Step 1: Upload files ────────────────────────────────────────────────────

st.markdown(
    "<div class='step-row'>"
    "<span class='step-badge'>1</span>"
    "<span class='step-title'>Upload Files</span>"
    "</div>",
    unsafe_allow_html=True,
)

col_cond, col_hplc = st.columns(2, gap="large")

with col_cond:
    with st.container(border=True):
        st.markdown("<div class='upload-card-label'>Experiment Conditions</div>", unsafe_allow_html=True)
        st.caption("Reactions, wells, timepoints, and roles.")

        with st.popover("Column guide", use_container_width=True):
            st.markdown(
                "| Column | Required? | Notes |\n"
                "|---|---|---|\n"
                "| **Reaction** | Yes | Unique reaction ID |\n"
                "| **Timepoint** | Yes | One row per timepoint |\n"
                "| **Plate_Well** | Yes | e.g. A1, B3 |\n"
                "| **Role** | Optional | Reactant or Product |\n"
                "| Ligand, Catalyst… | Optional | Extra condition columns |"
            )

        uploaded = st.file_uploader(
            "Upload conditions (.xlsx)",
            type=["xlsx"],
            label_visibility="collapsed",
        )
        if uploaded is not None:
            st.success(f"Loaded: {uploaded.name}")

with col_hplc:
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

    st.markdown(
        "<div class='step-row'>"
        "<span class='step-badge'>2</span>"
        "<span class='step-title'>Review & Configure</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        cfg_left, cfg_right = st.columns([1, 1.5])

        with cfg_left:
            st.markdown("<div class='section-label'>Plate editor</div>", unsafe_allow_html=True)
            st.session_state["show_plate_modal"] = st.toggle(
                "Enable", value=bool(st.session_state["show_plate_modal"])
            )

        with cfg_right:
            st.markdown("<div class='section-label'>Injections</div>", unsafe_allow_html=True)
            st.session_state["multi_injections"] = st.checkbox(
                "More than one injection?",
                value=bool(st.session_state["multi_injections"]),
            )
            if st.session_state["multi_injections"]:
                st.session_state["num_injections"] = st.number_input(
                    "Number of injections",
                    min_value=2, max_value=100,
                    value=max(2, int(st.session_state.get("num_injections", 2))),
                    step=1,
                    label_visibility="collapsed",
                )
            else:
                st.session_state["num_injections"] = 1
                st.markdown("<span class='info-pill'>1 injection</span>", unsafe_allow_html=True)

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
            if _svg_to_png:
                st.download_button(
                    "Download plate image (.png)",
                    data=_svg_to_png(svg),
                    file_name="plate_map.png",
                    mime="image/png",
                    use_container_width=True,
                    key="excel_dl_png",
                )
            else:
                st.download_button(
                    "Download plate image (.svg)",
                    data=svg,
                    file_name="plate_map.svg",
                    mime="image/svg+xml",
                    use_container_width=True,
                    key="excel_dl_svg",
                )

    # ── Step 3: Save & Proceed ─────────────────────────────────────────────
    st.markdown(
        "<div class='step-row'>"
        "<span class='step-badge'>3</span>"
        "<span class='step-title'>Save & Proceed</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    save_clicked = st.button("Save setup", type="primary", use_container_width=True, key="excel_save")

    if save_clicked:
        well_info = st.session_state.get("excel_plate_well_info") or build_well_info(reaction_rows, cond_cols)
        updated_rows = [well_info.get(r.get("Plate_Well", ""), dict(r)) for r in reaction_rows]
        role_lookup = {r["Reaction"]: r.get("Role", "Reactant") for r in reaction_rows}
        for r in updated_rows:
            if not str(r.get("Notes", "")).strip():
                r["Notes"] = "None"
            r.setdefault("Role", role_lookup.get(r.get("Reaction", ""), "Reactant"))

        st.session_state["experiment_setup"] = finalize_setup(
            "excel", updated_rows, timepoints, cond_cols, well_info, color_by
        )

        rxn_df = pd.DataFrame(updated_rows)
        st.session_state["experiment_setup_df"] = rxn_df

        raw_df = st.session_state.get("uploaded_excel_df")
        if isinstance(raw_df, pd.DataFrame) and not raw_df.empty:
            raw_df_norm = parsing_initial_input._normalize_cat_loading_df(raw_df)
            rxn_df_norm = parsing_initial_input._normalize_cat_loading_df(rxn_df)
            rxn_df_norm = rxn_df_norm.drop(columns=["well"], errors="ignore")
            annotated_df = raw_df_norm.merge(
                rxn_df_norm, on="Reaction", how="left", suffixes=("", "_rxn")
            )
            st.session_state["cat_loading_df"] = annotated_df
        st.success("Setup saved! Head to the Kinetics page to visualize your data.")


# ── Saved setup summary ────────────────────────────────────────────────────

setup = st.session_state.get("experiment_setup") or {}

if setup:
    st.divider()
    with st.container(border=True):
        st.markdown("**Saved Setup**")
        a, b, c, d = st.columns(4)
        a.metric("Reactions", len(setup.get("reaction_rows", [])))
        b.metric("Timepoints", len(setup.get("timepoints", [])))
        c.metric("Injections", int(setup.get("num_injections", 1)))
        hplc_name = st.session_state.get("hplc_file_name", "—")
        d.metric("HPLC File", hplc_name if hplc_name else "—")

        if st.button(
            "📈  Visualize data and initial rates →",
            type="primary",
            use_container_width=True,
            key="cta_kinetics",
        ):
            st.switch_page("pages/Kinetics.py")
