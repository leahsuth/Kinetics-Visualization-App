import pandas as pd
from typing import List, Optional

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


def find_catalyst_loading_column(cond_cols: List[str]) -> Optional[str]:
    """Match Catalyst_Loading / Catalyst Loading style headers."""
    for c in cond_cols:
        alnum = "".join(ch.lower() for ch in c if ch.isalnum())
        if alnum == "catalystloading":
            return c
        n = "_".join(str(c).strip().lower().split())
        if "catalyst" in n and "loading" in n:
            return c
    return None


def default_plate_color_field(cond_cols: List[str]) -> str:
    """Default 'Color wells by': catalyst loading if present, else first condition column, else Reaction."""
    cat = find_catalyst_loading_column(cond_cols)
    if cat:
        return cat
    if cond_cols:
        return cond_cols[0]
    return "Reaction"


def find_col_contains(columns, *needles: str) -> Optional[str]:
    cols = [str(c).strip() for c in columns]
    low = [c.lower() for c in cols]
    needles = [n.strip().lower() for n in needles if n and n.strip()]
    for n in needles:
        for i, c in enumerate(low):
            if c == n:
                return cols[i]
    # Prefer longer needles so e.g. "# of timepoints" wins over "tp" on odd headers.
    needles_sub = sorted(set(needles), key=len, reverse=True)
    for i, c in enumerate(low):
        for n in needles_sub:
            if n in c:
                return cols[i]
    return None




def parse_excel(df: pd.DataFrame) -> tuple[List[dict], List[str], List[str]]:
    df = normalize_headers(df)
    reaction_col = find_col_contains(df.columns, "reaction", "rxn")
    time_col = find_col_contains(
        df.columns,
        "# of timepoints",
        "number of timepoints",
        "num timepoints",
        "n timepoints",
        "timepoint count",
        "timepoint",
        "time point",
        "timepoints",
        "time",
        "tp",
    )
    well_col = find_col_contains(df.columns, "reaction_well", "reaction well", "plate_well", "plate well", "well")

    if reaction_col is None:
        raise ValueError('Missing required column containing "reaction".')
    if time_col is None:
        listed = ", ".join(repr(str(c)) for c in df.columns)
        raise ValueError(
            "Could not find a time column in the conditions file. "
            "ChemStation: use a **Timepoint** column (one row per time). "
            "Processed: use **# of Timepoints** (expected row count per reaction). "
            f"Your columns: {listed}"
        )

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
        r: dict = {"Reaction": rxn, "Reaction_Well": "", "Notes": "None"}
        if well_col:
            r["Reaction_Well"] = str(rxn_meta.loc[i, well_col]).strip()
        for c in cond_cols:
            r[c] = str(rxn_meta.loc[i, c]).strip()
        # Notes always starts as "None" when empty
        if not str(r.get("Notes", "")).strip():
            r["Notes"] = "None"
        rows.append(r)

    return rows, timepoints, cond_cols
