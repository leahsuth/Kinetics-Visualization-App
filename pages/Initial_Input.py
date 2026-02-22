# pages/initial_input.py
import re
import io
import sys
from pathlib import Path
from typing import Optional, Dict, List

import streamlit as st
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.page_styling.plate_selector import render_plate_editor_modal, generate_plate_svg  # noqa: E402


st.set_page_config(page_title="Experiment Setup", layout="wide")

st.markdown(
    """
    <style>
      .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1100px; }
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
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Experiment Setup")
st.caption("Define reactions, timepoints, and conditions — then visualise and edit the plate map.")

PLATE_MODE_OPTIONS = [
    "Use wells from file",
    "Auto-assign across (A1→A12, then B1…)",
    "Auto-assign down (A1→H1, then A2…)",
]

TEMPLATE_COLUMNS = ["Reaction", "Plate_Well", "Timepoint"]
TEMPLATE_OPTIONAL = ["Ligand", "Catalyst"]


def init_state() -> None:
    st.session_state.setdefault("experiment_setup", {})
    st.session_state.setdefault("plate_loading_mode", PLATE_MODE_OPTIONS[0])
    st.session_state.setdefault("show_plate_modal", True)
    st.session_state.setdefault("multi_injections", False)
    st.session_state.setdefault("num_injections", 1)
    st.session_state.setdefault("n_timepoints", 3)
    st.session_state.setdefault("timepoints", ["0 min", "5 min", "10 min"])
    st.session_state.setdefault("n_reactions", 3)
    st.session_state.setdefault("manual_cond_col_names", ["Ligand", "Catalyst"])
    st.session_state.setdefault("_manual_struct", None)
    st.session_state.setdefault(
        "manual_conditions_df",
        pd.DataFrame(
            [
                {"Reaction": "RXN_01", "Plate_Well": "A1", "Ligand": "", "Catalyst": "", "Notes": ""},
                {"Reaction": "RXN_02", "Plate_Well": "A2", "Ligand": "", "Catalyst": "", "Notes": ""},
                {"Reaction": "RXN_03", "Plate_Well": "A3", "Ligand": "", "Catalyst": "", "Notes": ""},
            ]
        ),
    )


init_state()


# ── helpers ────────────────────────────────────────────────────────────────


def resize_list(key: str, n: int, fill_value: str = "") -> None:
    arr = st.session_state.get(key, [])
    arr = (arr + [fill_value] * max(0, n - len(arr)))[:n]
    st.session_state[key] = arr


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


def generate_wells(n: int, mode: str) -> List[str]:
    rows = list("ABCDEFGH")
    cols = list(range(1, 13))
    wells = []
    if mode.startswith("Auto-assign across"):
        for r in rows:
            for c in cols:
                wells.append(f"{r}{c}")
    else:
        for c in cols:
            for r in rows:
                wells.append(f"{r}{c}")
    if n > len(wells):
        raise ValueError(f"Too many reactions ({n}) for a 96-well plate.")
    return wells[:n]


def excel_template_bytes() -> bytes:
    df = pd.DataFrame(
        [
            {"Reaction": "RXN_01", "Plate_Well": "A1", "Timepoint": "0 min", "Ligand": "LigA", "Catalyst": "Cat1"},
            {"Reaction": "RXN_02", "Plate_Well": "A2", "Timepoint": "5 min", "Ligand": "", "Catalyst": "Cat2"},
            {"Reaction": "", "Plate_Well": "", "Timepoint": "10 min", "Ligand": "", "Catalyst": ""},
        ]
    )
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Experiment")
    return buf.getvalue()


def parse_excel(df: pd.DataFrame) -> tuple[List[dict], List[str], List[str]]:
    df = normalize_headers(df)
    reaction_col = find_col_contains(df.columns, "reaction", "rxn")
    time_col = find_col_contains(df.columns, "timepoint", "time point", "timepoints", "tp")
    well_col = find_col_contains(df.columns, "plate_well", "plate well", "well")

    if reaction_col is None:
        raise ValueError('Missing required column containing "reaction".')
    if time_col is None:
        raise ValueError('Missing required column containing "timepoint".')

    timepoints = unique_preserve_order(clean_list(df[time_col].tolist()))
    if not timepoints:
        raise ValueError("No usable timepoints found.")

    excluded = {c for c in [reaction_col, time_col, well_col] if c}
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
        r: dict = {"Reaction": rxn, "Plate_Well": "", "Notes": ""}
        if well_col:
            r["Plate_Well"] = str(rxn_meta.loc[i, well_col]).strip()
        for c in cond_cols:
            r[c] = str(rxn_meta.loc[i, c]).strip()
        rows.append(r)

    return rows, timepoints, cond_cols


def ensure_manual_table_size(n: int, cond_cols: List[str]) -> None:
    df = st.session_state["manual_conditions_df"].copy()
    base_cols = ["Reaction", "Plate_Well"] + cond_cols + ["Notes"]
    for c in base_cols:
        if c not in df.columns:
            df[c] = ""
    df = df[base_cols]
    rows = df.to_dict(orient="records")
    new_rows = []
    for i in range(int(n)):
        if i < len(rows):
            new_rows.append(rows[i])
        else:
            new_rows.append({**{c: "" for c in base_cols}, "Reaction": f"RXN_{i+1:02d}"})
    st.session_state["manual_conditions_df"] = pd.DataFrame(new_rows)


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


def apply_plate_mode(reaction_rows: List[dict], mode: str) -> List[dict]:
    rows = [dict(r) for r in reaction_rows]
    if mode == "Use wells from file":
        for r in rows:
            r["Plate_Well"] = normalize_well(r.get("Plate_Well", "")) or str(r.get("Plate_Well", "")).strip()
        return rows
    wells = generate_wells(len(rows), mode)
    for i, r in enumerate(rows):
        r["Plate_Well"] = wells[i]
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
        "plate_loading_mode": st.session_state["plate_loading_mode"],
        "timepoints": timepoints,
        "condition_columns": cond_cols,
        "reaction_rows": reaction_rows,
        "reactions": reactions,
        "well_info": well_info,
        "color_by": color_by,
    }


# ── top settings bar ───────────────────────────────────────────────────────


with st.container(border=True):
    c1, c2, c3 = st.columns([2.5, 1.0, 1.5])

    with c1:
        st.markdown("<div class='section-label'>Well assignment</div>", unsafe_allow_html=True)
        st.session_state["plate_loading_mode"] = st.selectbox(
            "plate_loading_mode",
            options=PLATE_MODE_OPTIONS,
            index=PLATE_MODE_OPTIONS.index(st.session_state["plate_loading_mode"]),
            label_visibility="collapsed",
        )
        st.caption(
            "**Use wells from file** (default) reads well positions from your Excel. "
            "Auto-assign fills wells sequentially."
        )

    with c2:
        st.markdown("<div class='section-label'>Plate editor</div>", unsafe_allow_html=True)
        st.session_state["show_plate_modal"] = st.toggle(
            "Enable", value=bool(st.session_state["show_plate_modal"])
        )

    with c3:
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


# ── input section ──────────────────────────────────────────────────────────


with st.container(border=True):
    mode = st.radio("Input method", options=["Upload Excel", "Manual entry"], horizontal=True)

    # ── Excel upload ──────────────────────────────────────────────────────
    if mode == "Upload Excel":
        st.markdown(
            "> **Getting started:** Download the template below, fill it in, then re-upload. "
            "Or upload your own Excel — any extra columns are treated as condition fields automatically.",
            unsafe_allow_html=False,
        )

        dl_col, info_col = st.columns([1, 1])
        with dl_col:
            st.download_button(
                label="Download template (.xlsx)",
                data=excel_template_bytes(),
                file_name="experiment_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with info_col:
            with st.expander("Template column guide", expanded=False):
                st.markdown(
                    "| Column | Required? | Notes |\n"
                    "|---|---|---|\n"
                    "| **Reaction** | Yes | Unique reaction ID |\n"
                    "| **Timepoint** | Yes | One row per timepoint |\n"
                    "| **Plate_Well** | If using 'wells from file' | e.g. A1, B3 |\n"
                    "| Ligand, Catalyst, … | Optional | Any extra columns become conditions |"
                )

        uploaded = st.file_uploader("Upload completed template (.xlsx)", type=["xlsx"])

        if uploaded is not None:
            try:
                df = pd.read_excel(uploaded)
                if df.empty:
                    st.error("This Excel file appears to be empty.")
                    st.stop()
                reaction_rows, timepoints, cond_cols = parse_excel(df)
                reaction_rows = apply_plate_mode(reaction_rows, st.session_state["plate_loading_mode"])
            except Exception as e:
                st.error(str(e))
                st.stop()

            m1, m2, m3 = st.columns(3)
            m1.metric("Reactions", len(reaction_rows))
            m2.metric("Timepoints", len(timepoints))
            m3.metric("Injections", int(st.session_state["num_injections"]))

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
                        "Download plate image (.svg)",
                        data=svg,
                        file_name="plate_map.svg",
                        mime="image/svg+xml",
                        use_container_width=True,
                        key="excel_dl_svg",
                    )

            st.divider()
            if st.button("Save setup", type="primary", use_container_width=True, key="excel_save"):
                well_info = st.session_state.get("excel_plate_well_info") or build_well_info(reaction_rows, cond_cols)
                updated_rows = [well_info.get(r.get("Plate_Well", ""), dict(r)) for r in reaction_rows]
                st.session_state["experiment_setup"] = finalize_setup(
                    "excel", updated_rows, timepoints, cond_cols, well_info, color_by
                )
                st.success("Setup saved.")

    # ── Manual entry ──────────────────────────────────────────────────────
    else:
        # ── Condition column editor ────────────────────────────────────────
        with st.expander("Condition columns", expanded=True):
            st.caption("Define custom column names. Click + / − to add or remove columns.")
            col_names: List[str] = list(st.session_state["manual_cond_col_names"])

            btn_l, btn_r, _ = st.columns([1, 1, 5])
            if btn_l.button("＋ Add column", key="add_cond_col"):
                col_names.append(f"Condition {len(col_names) + 1}")
            if btn_r.button("− Remove last", key="rm_cond_col", disabled=len(col_names) == 0):
                col_names = col_names[:-1]

            if col_names:
                name_inputs = st.columns(min(len(col_names), 4))
                for i, name in enumerate(col_names):
                    with name_inputs[i % 4]:
                        col_names[i] = st.text_input(
                            f"Col {i + 1}",
                            value=name,
                            key=f"cond_col_name_{i}",
                            placeholder=f"e.g. Ligand",
                        )

            # deduplicate silently (keep first occurrence)
            seen_names: set = set()
            deduped: List[str] = []
            for n in col_names:
                n = n.strip() or f"Column_{len(deduped)+1}"
                if n not in seen_names:
                    seen_names.add(n)
                    deduped.append(n)
            col_names = deduped
            st.session_state["manual_cond_col_names"] = col_names

        cond_cols = col_names

        # ── Counts ────────────────────────────────────────────────────────
        left, right = st.columns([1, 2])
        with left:
            st.session_state["n_reactions"] = int(
                st.number_input("Reactions", min_value=1, max_value=200,
                                value=int(st.session_state["n_reactions"]), step=1)
            )
            st.session_state["n_timepoints"] = int(
                st.number_input("Timepoints", min_value=1, max_value=200,
                                value=int(st.session_state["n_timepoints"]), step=1)
            )

        with right:
            st.markdown("**Global timepoints**")
            resize_list("timepoints", st.session_state["n_timepoints"], "")
            tp_cols = st.columns(min(st.session_state["n_timepoints"], 4))
            for i in range(st.session_state["n_timepoints"]):
                with tp_cols[i % 4]:
                    st.session_state["timepoints"][i] = st.text_input(
                        f"TP {i+1}", value=st.session_state["timepoints"][i],
                        placeholder="e.g. 0 min", key=f"tp_input_{i}",
                    )

        # Only rebuild the table structure when n_reactions or column names actually change
        # (not on every rerun — this was causing edits to vanish on Enter-key press)
        current_struct = (int(st.session_state["n_reactions"]), tuple(cond_cols))
        if st.session_state.get("_manual_struct") != current_struct:
            ensure_manual_table_size(st.session_state["n_reactions"], cond_cols)
            st.session_state["_manual_struct"] = current_struct

        edited = st.data_editor(
            st.session_state["manual_conditions_df"],
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            key="manual_data_editor",
        )
        # Save immediately so the next rerun reads the committed edits
        st.session_state["manual_conditions_df"] = edited.copy()

        timepoints = unique_preserve_order(clean_list(st.session_state["timepoints"]))
        reaction_rows = apply_plate_mode(edited.to_dict(orient="records"), st.session_state["plate_loading_mode"])

        color_choices = ["Reaction"] + cond_cols
        color_by = st.selectbox(
            "Color wells by",
            options=color_choices,
            index=0,
            key="manual_color_by",
            help="Choose which field drives well colors in the plate map.",
        )

        if st.session_state["show_plate_modal"]:
            base_info = build_well_info(reaction_rows, cond_cols)
            with st.container(border=True):
                well_info_manual = render_plate_editor_modal(
                    base_info,
                    title="Plate Map",
                    key_prefix="manual_plate",
                    n_items=len(reaction_rows),
                    color_by=color_by,
                )
                st.session_state["manual_plate_well_info"] = well_info_manual
                svg = generate_plate_svg(well_info_manual, color_by, len(reaction_rows))
                st.download_button(
                    "Download plate image (.svg)",
                    data=svg,
                    file_name="plate_map.svg",
                    mime="image/svg+xml",
                    use_container_width=True,
                    key="manual_dl_svg",
                )

        st.divider()
        if st.button("Save setup", type="primary", use_container_width=True, key="manual_save"):
            if len(timepoints) != st.session_state["n_timepoints"]:
                st.error("Fill in all timepoints before saving.")
                st.stop()

            well_info = st.session_state.get("manual_plate_well_info") or build_well_info(reaction_rows, cond_cols)
            updated_rows = [well_info.get(r.get("Plate_Well", ""), dict(r)) for r in reaction_rows]
            st.session_state["experiment_setup"] = finalize_setup(
                "manual", updated_rows, timepoints, cond_cols, well_info, color_by
            )
            st.success("Setup saved.")


# ── saved setup summary ────────────────────────────────────────────────────


setup = st.session_state.get("experiment_setup") or {}
if setup:
    with st.container(border=True):
        st.subheader("Saved setup")
        a, b, c, d = st.columns(4)
        a.metric("Source", setup.get("source", "—").capitalize())
        b.metric("Reactions", len(setup.get("reaction_rows", [])))
        c.metric("Timepoints", len(setup.get("timepoints", [])))
        d.metric("Injections", int(setup.get("num_injections", 1)))

        if setup.get("well_info"):
            col_by = setup.get("color_by", "Reaction")
            svg = generate_plate_svg(setup["well_info"], col_by, len(setup.get("reaction_rows", [])) or 1)
            st.download_button(
                "Download plate image (.svg)",
                data=svg,
                file_name="plate_map_saved.svg",
                mime="image/svg+xml",
                use_container_width=True,
                key="saved_dl_svg",
            )
else:
    st.caption("No setup saved yet.")
