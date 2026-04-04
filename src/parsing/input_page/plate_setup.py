from typing import Optional, Dict, List
import re

def build_well_info(reaction_rows: List[dict], cond_cols: List[str]) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for r in reaction_rows:
        well = str(r.get("Reaction_Well", "")).strip()
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
        r["Reaction_Well"] = normalize_well(r.get("Reaction_Well", "")) or str(r.get("Reaction_Well", "")).strip()
    return rows

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

def finalize_setup(
    source: str, reaction_rows: List[dict], timepoints: List[str],
    cond_cols: List[str], well_info: Dict[str, dict], color_by: str = "Reaction"
) -> dict:
    reactions = []
    for r in reaction_rows:
        rxn = str(r.get("Reaction", "")).strip()
        well = str(r.get("Reaction_Well", "")).strip()
        cond_bits = [f"{c}:{str(r.get(c,'') or '').strip()}" for c in cond_cols if str(r.get(c, "") or "").strip()]
        suffix = " | " + "  ".join(cond_bits) if cond_bits else ""
        reactions.append(f"{rxn} | {well}{suffix}")
    return {
        "source": source,
        "timepoints": timepoints,
        "condition_columns": cond_cols,
        "reaction_rows": reaction_rows,
        "reactions": reactions,
        "well_info": well_info,
        "color_by": color_by,
    }
