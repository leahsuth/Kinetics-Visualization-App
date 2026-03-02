# THIS WILL BE TO PARSE THE CAT LOADING FILES INTO A DATAFRAME
import pandas as pd
from pathlib import Path
from typing import Union

import openpyxl  # needed for excel file -> df


def _normalize_cat_loading_df(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize column names; map time/reaction/well columns. Returns a copy."""
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
        .str.extract(r"(\d+)", expand=False)  # take first group of digits
    )
    # Convert to integer; rows without digits become NA
    df["Reaction"] = pd.to_numeric(rxn_num, errors="coerce").astype("Int64")

    return df


def parse_cat_loading_file(file_path_or_df: Union[str, Path, pd.DataFrame],
                           save_as_csv: bool = False):
    """Parse a cat-loading-style Excel (or already-loaded DataFrame) into a cleaned DataFrame."""

    # If the input is a DataFrame, normalize it and return it
    if isinstance(file_path_or_df, pd.DataFrame):
        df = _normalize_cat_loading_df(file_path_or_df)
        if save_as_csv:
            out = file_path_or_df.with_suffix(".csv")
            df.to_csv(out, index=False)
        return df

    # If the input is a string, convert it to a Path object
    if isinstance(file_path_or_df, str):
        path = Path(file_path_or_df)
    # If the input is a Path object, use it directly
    else:
        path = file_path_or_df

    # Read the Excel file into a DataFrame
    df = pd.read_excel(path)
    df = _normalize_cat_loading_df(df)
    if save_as_csv:
        out = path.with_suffix(".csv")
        df.to_csv(out, index=False)
    return df


def timepoint_map(df):
    time_df = df["time"].dropna()
    return dict(enumerate(time_df.astype(str).tolist()))


def num_reactions(df):
    return df['Reaction'].nunique()


def cols_per_timepoint(df):
    col_num = (
        df["well"].astype(str).str.extract(r"(\d+)$").astype(int)[0]
    )
    return int(col_num.max())


if __name__ == "__main__":
    df_excel = parse_cat_loading_file(
        "./data/NB-0123-0005_Cat_Loading_Conditions.xlsx", True
    )
    print(timepoint_map(df_excel))
