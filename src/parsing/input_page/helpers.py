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




def parse_excel(df: pd.DataFrame) -> tuple[List[dict], List[str], List[str]]:
    df = normalize_headers(df)
    reaction_col = find_col_contains(df.columns, "reaction", "rxn")
    time_col = find_col_contains(df.columns, "timepoint", "time point", "timepoints", "tp")
    well_col = find_col_contains(df.columns, "reaction_well", "reaction well", "plate_well", "plate well", "well")

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
