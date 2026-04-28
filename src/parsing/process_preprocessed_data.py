import pandas as pd

from src.parsing.input_page.helpers import find_col_contains
from src.parsing.parsing_cat_loading_conditions import process_conditions_file


def normalize_preprocessed_conditions(file_name):
    """
    Load and normalize the *processed-mode* conditions sheet.

    Expected minimum fields are:
    - Reaction
    - # of Timepoints (or equivalent label recognized by `find_col_contains`)
    """
    # Load and normalize the conditions file.
    df = process_conditions_file(file_name)

    # Normalize alternate reaction headers (e.g., "rxn") to "Reaction".
    rxn_col = find_col_contains(df.columns, "Reaction", "reaction", "rxn", "RXN", "REACTION")
    if rxn_col and rxn_col != "Reaction":
        df = df.rename(columns={rxn_col: "Reaction"})
    # Throw error if the reaction column is not found.
    if "Reaction" not in df.columns:
        raise ValueError('Conditions file is missing a "Reaction" column.')

    # Normalize the time column to "Num_Timepoints".
    time_col = find_col_contains(
        df.columns, "Num_Timepoints", "Time",
        "timepoint", "Timepoint", "TP", "Time Point")
    if time_col:
        df = df.rename(columns={time_col: "Num_Timepoints"})

    # Throw error if the time column is not found.
    if "Num_Timepoints" not in df.columns:
        raise ValueError(
            'Conditions file is missing a "Num_Timepoints" column.')
    
    # Normalize the well column to "Reaction_Well".
    well_col = find_col_contains(
        df.columns, "Reaction_Well", "Plate Well", "Plate well",
        "well", "Well", "Reaction Well", "Plate_Well")
    if well_col:
        df = df.rename(columns={well_col: "Reaction_Well"})

    return df


def _rxn_key(val) -> str:
    """
    Canonical reaction ID used for joins/comparisons:
    - trims whitespace
    - drops empty/"nan"
    - maps numeric-looking values (1, 1.0, "1") -> "1"
    """
    s = str(val).strip()
    if not s or s.lower() == "nan":
        return ""
    num = pd.to_numeric(s, errors="coerce")
    if pd.notna(num) and float(num).is_integer():
        return str(int(num))
    return s


def _get_expected_timepoints_by_reaction(
    conditions_df: pd.DataFrame,
) -> dict[str, int]:
    """
    Read expected row counts by reaction from columns:
    - Reaction
    - # of Timepoints
    """
    timepoints_col = "Num_Timepoints"

    # Build a map: reaction_id -> expected number of rows in measurements.
    expected: dict[str, int] = {}
    for _, row in conditions_df.iterrows():
        rxn = _rxn_key(row["Reaction"])
        if not rxn:
            # Ignore blank reaction rows in the conditions sheet.
            continue
        n = pd.to_numeric(row[timepoints_col], errors="coerce")
        if pd.isna(n) or float(n) <= 0:
            raise ValueError(f'Reaction {rxn} has invalid "Num_Timepoints": '
                             f"{row[timepoints_col]!r}")
        n_int = int(round(float(n)))
        # Guard against contradictory duplicate reaction rows.
        if rxn in expected and expected[rxn] != n_int:
            raise ValueError(
                f'Reaction {rxn} has conflicting "Num_Timepoints" values '
                "in conditions."
            )
        expected[rxn] = n_int

    if not expected:
        raise ValueError(
            'No valid Reaction + "Num_Timepoints" rows found in conditions file.'
        )
    return expected


def _validate_timepoints(
    meas_df: pd.DataFrame,
    conditions_df: pd.DataFrame,
) -> None:
    """
    Confirm measurement row counts per Reaction match
    "Num_Timepoints" from conditions.
    """
    expected = _get_expected_timepoints_by_reaction(conditions_df)
    raw_actual = meas_df.groupby("Reaction").size().to_dict()
    actual = {_rxn_key(k): int(v) for k, v in raw_actual.items() if _rxn_key(k)}

    if actual != expected:
        raise ValueError("Timepoint row mismatch.")


def process_preprocessed_data(
    file_name: str,
    conditions_df: pd.DataFrame,
    save_as_csv: bool = False,
) -> pd.DataFrame:
    """
    Process preprocessed measurements into a normalized dataframe.
    """
    df = normalize_preprocessed_conditions(file_name)

    # Normalize alternate reaction headers (e.g., "rxn") to "Reaction".
    rxn_col = find_col_contains(df.columns, "reaction", "rxn")
    if rxn_col and rxn_col != "Reaction":
        df = df.rename(columns={rxn_col: "Reaction"})
    # Throw error if the reaction column is not found.
    if "Reaction" not in df.columns:
        raise ValueError('Preprocessed data file is missing a "Reaction" column.')

    # Normalize the time column to "time".
    time_col = find_col_contains(df.columns, "Time", "time", "TIME", "times", "Time Point")
    if time_col:
        df = df.rename(columns={time_col: "time"})

    # Throw error if the time column is not found.
    if "time" not in df.columns:
        raise ValueError('Preprocessed data file is missing a "time" column.')

    # Normalize the column names
    df.columns = [str(c).strip() for c in df.columns]

    if save_as_csv:
        df.to_csv(file_name.with_suffix(".csv"), index=False)

    # Validate the data vs the conditions.
    _validate_timepoints(df, conditions_df)

    return df


def add_loading_data_preprocessed(df, conditions_df):
    merged = df.copy()
    lookup_copy = conditions_df.copy()
    lookup_copy = lookup_copy.drop(columns=["Num_Timepoints", "Reaction_Well"], errors="ignore")

    lookup_copy = lookup_copy.drop_duplicates(subset=["Reaction"], keep="first")

    # Avoid duplicate columns after merge (case/spacing-insensitive).
    existing_norm = {
        str(c).strip().lower().replace(" ", "_") for c in merged.columns
    }
    keep_cols = ["Reaction"]
    for c in lookup_copy.columns:
        if c == "Reaction":
            continue
        c_norm = str(c).strip().lower().replace(" ", "_")
        if c_norm not in existing_norm:
            keep_cols.append(c)

    lookup_copy = lookup_copy[keep_cols]
    merged = pd.merge(merged, lookup_copy, on="Reaction", how="left")

    return merged
