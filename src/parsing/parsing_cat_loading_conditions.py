"""
Parse catalyst-loading / experiment conditions from .csv, .xlsx, .xls, and .xlsm.
"""

from pathlib import Path
from typing import Union

import pandas as pd


def _normalize_conditions_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize column names.

    Parameters
    ----------
    df : pd.DataFrame
        Raw conditions table from Excel or CSV.

    Returns
    -------
    pd.DataFrame
        Normalized conditions table.
    """
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all").copy()
    df.columns = df.columns.astype(str).str.strip()
    df.columns = df.columns.str.replace(" ", "_")
    df.columns = df.columns.str.replace("(", "")
    df.columns = df.columns.str.replace(")", "")
    df.columns = df.columns.str.replace("/", "_")
    df.columns = df.columns.str.replace(":", "_")
    df.columns = df.columns.str.replace(";", "_")
    df.columns = df.columns.str.replace(".", "_")
    df.columns = df.columns.str.replace(",", "_")
    df.columns = df.columns.str.lower()

    new_cols = {}
    for c in df.columns:
        if "time" in c.lower():
            new_cols[c] = "time"
        if "reaction" in c.lower():
            new_cols[c] = "Reaction"
        if "well" in c.lower():
            new_cols[c] = "well"
    df = df.rename(columns=new_cols)

    rxn_num = (
        df["Reaction"]
        .astype(str)
        .str.extract(r"(\d+)", expand=False)
    )
    df["Reaction"] = pd.to_numeric(rxn_num, errors="coerce").astype("Int64")

    return df


def _read_raw_conditions(file_name, ext: str) -> pd.DataFrame:
    """
    Read conditions from disk path or file-like (no normalization).

    Parameters
    ----------
    file_name : str, Path, or file-like
        Path or upload buffer (``seek(0)`` before read when file-like).
    ext : str
        Lowercase suffix from the path or upload ``.name`` (may be ``""``).
    """
    is_buffer = not isinstance(file_name, (str, Path))
    if is_buffer:
        try:
            file_name.seek(0)
        except Exception:
            pass

    if ext == ".csv":
        return pd.read_csv(file_name)

    if ext == ".xls":
        return pd.read_excel(file_name, engine="xlrd")

    if ext in (".xlsx", ".xlsm"):
        return pd.read_excel(file_name, engine="openpyxl")

    # Uploaded buffers sometimes omit an extension; assume modern Excel.
    if not ext and is_buffer:
        return pd.read_excel(file_name, engine="openpyxl")

    raise ValueError(f"Unsupported conditions file type: {ext!r}")


def process_conditions_file(file_name, save_as_csv: bool = False) -> pd.DataFrame:
    """
    Load conditions from CSV or Excel into a normalized dataframe.

    Parameters
    ----------
    file_name : str, pathlib.Path, or file-like
        Path to file or Streamlit ``UploadedFile`` (must have ``.name`` for uploads).
    save_as_csv : bool
        If True, write the **normalized** table next to the source as ``.csv``.

    Returns
    -------
    pd.DataFrame
        Normalized conditions table.
    """
    if isinstance(file_name, (str, Path)):
        filepath = Path(file_name)
    else:
        fname = getattr(file_name, "name", None)
        if not fname:
            raise TypeError("file_name must have a .name attribute when not a path.")
        filepath = Path(fname)

    ext = filepath.suffix.lower()
    if not ext and not isinstance(file_name, (str, Path)):
        ext = ".xlsx"

    out_path = filepath.with_suffix(".csv")

    raw = _read_raw_conditions(file_name, ext)
    df = _normalize_conditions_df(raw)

    if save_as_csv:
        df.to_csv(out_path, index=False)

    return df


def parse_conditions_df(
    file_path_or_df: Union[str, Path, pd.DataFrame],
    save_as_csv: bool = False,
) -> pd.DataFrame:
    """
    Normalize conditions from a file path, upload, or an existing DataFrame.

    Parameters
    ----------
    file_path_or_df : str, pathlib.Path, pandas.DataFrame, or file-like
        Same as ``process_conditions_file`` when not a DataFrame.
    save_as_csv : bool
        Passed through when loading from a file; not allowed for DataFrame input.

    Returns
    -------
    pd.DataFrame
        Normalized conditions table.
    """
    if isinstance(file_path_or_df, pd.DataFrame):
        df = _normalize_conditions_df(file_path_or_df)
        if save_as_csv:
            raise ValueError(
                "save_as_csv is not supported when the input is a DataFrame."
            )
        return df

    return process_conditions_file(file_path_or_df, save_as_csv=save_as_csv)


def timepoint_map(df):
    """
    Map the timepoints to a dictionary.

    Parameters
    ----------
    df : pd.DataFrame
        The initial input dataframe.

    Returns
    -------
    dict
        Enumeration index to timepoint label.
    """
    time_df = df["time"].dropna()
    return dict(enumerate(time_df.astype(str).tolist()))


def num_reactions(df):
    """
    Number of distinct reactions in the conditions dataframe.

    Parameters
    ----------
    df : pd.DataFrame
        The initial input dataframe.

    Returns
    -------
    int
        Count of unique ``Reaction`` values.
    """
    return df["Reaction"].nunique()
