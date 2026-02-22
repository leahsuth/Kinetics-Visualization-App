# src/page_styling/plate_selector.py
import json
import math
import hashlib
import string
from typing import Dict, Tuple, Optional, List

import streamlit as st
import streamlit.components.v1 as components


def list_of_letters(n: int) -> List[str]:
    return list(string.ascii_uppercase[: max(0, int(n))])


def _well_to_rc(well: str) -> Optional[Tuple[int, int]]:
    try:
        w = str(well).strip().upper()
        row = w[0]
        col = int(w[1:])
        if row < "A" or row > "H":
            return None
        if col < 1 or col > 12:
            return None
        return (ord(row) - ord("A"), col - 1)
    except Exception:
        return None


def _dims_from_wells(wells: List[str]) -> Tuple[int, int]:
    max_r, max_c = 0, 0
    for w in wells:
        rc = _well_to_rc(w)
        if rc is None:
            continue
        r, c = rc
        max_r = max(max_r, r)
        max_c = max(max_c, c)
    return (max_r + 1, max_c + 1)


def compute_plate_dims(
    n_items: int,
    wells_hint: Optional[List[str]] = None,
    max_rows: int = 8,
    max_cols: int = 12,
) -> Tuple[int, int]:
    n_items = max(1, int(n_items))
    best_rows, best_cols = max_rows, max_cols
    best_area = best_rows * best_cols

    for rows in range(1, max_rows + 1):
        cols = math.ceil(n_items / rows)
        if cols <= max_cols:
            area = rows * cols
            if area < best_area:
                best_rows, best_cols = rows, cols
                best_area = area

    rows, cols = best_rows, best_cols

    if wells_hint:
        need_r, need_c = _dims_from_wells(wells_hint)
        rows = min(max_rows, max(rows, need_r))
        cols = min(max_cols, max(cols, need_c))

    return rows, cols


def value_to_color(value: str) -> str:
    s = (value or "").strip()
    if not s:
        return "#ebebeb"
    h = hashlib.md5(s.encode("utf-8")).hexdigest()
    r = int(int(h[0:2], 16) * 0.5 + 127)
    g = int(int(h[2:4], 16) * 0.5 + 127)
    b = int(int(h[4:6], 16) * 0.5 + 127)
    return f"#{r:02x}{g:02x}{b:02x}"


@st.dialog("Edit Well", width="small")
def _edit_well_dialog(well_id: str, info: Dict[str, dict], key_prefix: str) -> None:
    d = dict(info.get(well_id, {}))

    st.markdown(
        f"<span style='font-size:1.1rem;font-weight:700;'>Well "
        f"<code style='background:#f0f2f6;padding:2px 8px;border-radius:6px;'>{well_id}</code></span>",
        unsafe_allow_html=True,
    )
    st.markdown("")

    d["Reaction"] = st.text_input(
        "Reaction ID", value=str(d.get("Reaction", "") or ""),
        key=f"{key_prefix}_dlg_rxn_{well_id}",
    )

    editable = sorted([
        k for k in d
        if k not in {"Reaction", "Notes", "Plate_Well", "_custom_color", "Conditions", "Label"}
    ])
    for k in editable:
        d[k] = st.text_input(
            k, value=str(d.get(k, "") or ""),
            key=f"{key_prefix}_dlg_{k}_{well_id}",
        )

    d["Notes"] = st.text_area(
        "Notes", value=str(d.get("Notes", "") or ""), height=80,
        key=f"{key_prefix}_dlg_notes_{well_id}",
    )

    st.markdown("**Custom color** (overrides auto color)")
    cc1, cc2 = st.columns([3, 1])
    with cc1:
        current_color = str(d.get("_custom_color") or "#EDEDED").strip()
        d["_custom_color"] = st.color_picker(
            "color", value=current_color,
            key=f"{key_prefix}_dlg_color_{well_id}",
            label_visibility="collapsed",
        )
    with cc2:
        if st.button("Reset", key=f"{key_prefix}_dlg_reset_{well_id}", use_container_width=True):
            d["_custom_color"] = "#EDEDED"

    st.markdown("")
    b1, b2 = st.columns(2)
    with b1:
        if st.button("Save", type="primary", use_container_width=True, key=f"{key_prefix}_dlg_save_{well_id}"):
            info[well_id] = d
            st.session_state[f"{key_prefix}_well_info"] = info
            st.session_state[f"{key_prefix}_active_well"] = None
            st.rerun()
    with b2:
        if st.button("Cancel", use_container_width=True, key=f"{key_prefix}_dlg_cancel_{well_id}"):
            st.session_state[f"{key_prefix}_active_well"] = None
            st.rerun()


def generate_plate_svg(info: Dict[str, dict], color_by: str, n_items: int) -> str:
    """Return an SVG string of the plate map, suitable for download."""
    wells = sorted(info.keys(), key=lambda w: (_well_to_rc(w) or (99, 99)))
    num_rows, num_cols = compute_plate_dims(max(1, int(n_items)), wells_hint=wells)
    rows = list_of_letters(num_rows)
    cols = list(range(1, num_cols + 1))

    cell = 52
    pad = 28
    lw = 26   # row-label width
    lh = 22   # col-label height
    W = pad * 2 + lw + num_cols * cell
    H = pad * 2 + lh + num_rows * cell

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">',
        f'<rect width="{W}" height="{H}" fill="#ffffff" rx="8"/>',
    ]

    for j, c in enumerate(cols):
        x = pad + lw + j * cell + cell // 2
        y = pad + lh // 2
        parts.append(f'<text x="{x}" y="{y}" text-anchor="middle" dominant-baseline="middle" '
                     f'font-family="Arial" font-size="11" fill="#999">{c}</text>')

    for i, r in enumerate(rows):
        rx = pad + lw // 2
        ry = pad + lh + i * cell + cell // 2
        parts.append(f'<text x="{rx}" y="{ry}" text-anchor="middle" dominant-baseline="middle" '
                     f'font-family="Arial" font-size="11" fill="#999">{r}</text>')

        for j, c in enumerate(cols):
            well_id = f"{r}{c}"
            d = info.get(well_id, {})
            custom = str(d.get("_custom_color") or "").strip()
            color = custom if (custom and custom != "#EDEDED") else value_to_color(str(d.get(color_by, "") or "").strip()) if well_id in info else "#ebebeb"
            cx = pad + lw + j * cell + cell // 2
            cy = pad + lh + i * cell + cell // 2
            r_circ = cell // 2 - 4
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r_circ}" fill="{color}" stroke="rgba(0,0,0,0.15)" stroke-width="1.2"/>')
            if well_id in info:
                parts.append(f'<text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="middle" '
                             f'font-family="Arial" font-size="8" font-weight="bold" fill="#333">{well_id}</text>')

    parts.append('</svg>')
    return "\n".join(parts)


def _render_legend(info: Dict[str, dict], color_by: str) -> None:
    seen: Dict[str, str] = {}
    for d in info.values():
        v = str(d.get(color_by, "") or "").strip()
        if v and v not in seen:
            custom = str(d.get("_custom_color") or "").strip()
            seen[v] = custom if (custom and custom != "#EDEDED") else value_to_color(v)
    if not seen:
        return
    swatches = "".join(
        f"<span style='display:inline-flex;align-items:center;gap:5px;"
        f"margin-right:14px;font-size:0.82rem;white-space:nowrap;'>"
        f"<span style='display:inline-block;width:12px;height:12px;border-radius:50%;"
        f"background:{color};border:1px solid rgba(0,0,0,.15);'></span>{label}</span>"
        for label, color in seen.items()
    )
    st.markdown(
        f"<div style='padding:4px 0 10px;display:flex;flex-wrap:wrap;gap:4px 0;'>{swatches}</div>",
        unsafe_allow_html=True,
    )


def _inject_well_colors(well_colors: Dict[str, str]) -> None:
    """Inject JS into parent page to color well buttons by their text label."""
    colors_js = json.dumps(well_colors)
    components.html(
        f"""<script>
        (function() {{
            var colors = {colors_js};
            function apply() {{
                try {{
                    var btns = window.parent.document.querySelectorAll(
                        '[data-testid="stButton"] button'
                    );
                    btns.forEach(function(btn) {{
                        var t = btn.textContent.trim();
                        if (colors[t] !== undefined) {{
                            btn.style.setProperty('background', colors[t], 'important');
                            btn.style.setProperty('border-radius', '50%', 'important');
                            btn.style.setProperty('width', '52px', 'important');
                            btn.style.setProperty('height', '52px', 'important');
                            btn.style.setProperty('font-size', '0.70rem', 'important');
                            btn.style.setProperty('font-weight', '700', 'important');
                            btn.style.setProperty('border', '2px solid rgba(49,51,63,.18)', 'important');
                        }}
                    }});
                }} catch(e) {{}}
            }}
            setTimeout(apply, 50);
            setTimeout(apply, 300);
            setTimeout(apply, 800);
        }})();
        </script>""",
        height=0,
        scrolling=False,
    )


def render_plate_editor_modal(
    well_info: Dict[str, dict],
    title: str,
    key_prefix: str,
    n_items: int,
    color_by: str,
    show_labels: bool = True,
) -> Dict[str, dict]:
    st.session_state.setdefault(f"{key_prefix}_active_well", None)

    # Merge: add new wells, preserve edits on existing ones
    stored = st.session_state.get(f"{key_prefix}_well_info", {})
    for well, data in (well_info or {}).items():
        if well not in stored:
            stored[well] = dict(data)
    st.session_state[f"{key_prefix}_well_info"] = stored

    info = st.session_state[f"{key_prefix}_well_info"]
    active = st.session_state[f"{key_prefix}_active_well"]
    wells = sorted(info.keys(), key=lambda w: (_well_to_rc(w) or (99, 99)))
    num_rows, num_cols = compute_plate_dims(max(1, int(n_items)), wells_hint=wells)

    rows = list_of_letters(num_rows)
    cols = [str(i) for i in range(1, num_cols + 1)]
    col_weights = [0.38] + [1] * num_cols

    def well_color(w: str) -> str:
        d = info.get(w, {})
        custom = str(d.get("_custom_color") or "").strip()
        if custom and custom != "#EDEDED":
            return custom
        v = str(d.get(color_by, "") or "").strip()
        return value_to_color(v)

    # ── header ──────────────────────────────────────────────────────────────
    st.markdown(
        f"<div style='font-size:1.05rem;font-weight:700;margin-bottom:2px;'>{title}</div>"
        f"<div style='font-size:0.80rem;color:rgba(49,51,63,.5);margin-bottom:4px;'>"
        f"Colored by <b>{color_by}</b> · click a well to edit</div>",
        unsafe_allow_html=True,
    )
    _render_legend(info, color_by)

    # ── grid ────────────────────────────────────────────────────────────────
    header_cols = st.columns(col_weights)
    header_cols[0].markdown("")
    for idx, col_num in enumerate(cols):
        header_cols[idx + 1].markdown(
            f"<div style='text-align:center;font-weight:700;font-size:0.78rem;"
            f"color:rgba(49,51,63,.45);'>{col_num}</div>",
            unsafe_allow_html=True,
        )

    well_colors: Dict[str, str] = {}
    for r in rows:
        row_cols = st.columns(col_weights)
        row_cols[0].markdown(
            f"<div style='text-align:right;padding-right:6px;padding-top:14px;"
            f"font-weight:700;font-size:0.85rem;color:rgba(49,51,63,.55);'>{r}</div>",
            unsafe_allow_html=True,
        )
        for i, c in enumerate(cols):
            well_id = f"{r}{c}"
            color = well_color(well_id) if well_id in info else "#ebebeb"
            well_colors[well_id] = color

            with row_cols[i + 1]:
                if st.button(well_id, key=f"{key_prefix}_well_{well_id}"):
                    st.session_state[f"{key_prefix}_active_well"] = well_id
                    st.rerun()

                if show_labels and well_id in info:
                    label = str(info[well_id].get(color_by, "") or "").strip()
                    st.markdown(
                        f"<div style='font-size:0.65rem;color:rgba(49,51,63,.6);"
                        f"text-align:center;overflow:hidden;text-overflow:ellipsis;"
                        f"white-space:nowrap;max-width:52px;margin-top:-4px;'>{label}</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown("<div style='min-height:0.9rem;'></div>", unsafe_allow_html=True)

    # ── inject JS to apply colors to buttons ────────────────────────────────
    _inject_well_colors(well_colors)

    # ── open edit dialog when a well is clicked ──────────────────────────────
    if active and active in info:
        _edit_well_dialog(active, info, key_prefix)

    return info
