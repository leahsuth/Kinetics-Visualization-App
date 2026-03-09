# THIS WILL BE TO PARSE THE CAT LOADING FILES INTO A DATAFRAME
import pandas as pd
from pathlib import Path
from typing import Union


def _normalize_cat_loading_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize column names

    Parameters
    ----------
    df : pd.DataFrame
        The initial input dataframe to clean and standardize.
    Returns
    -------
    df : pd.DataFrame
        The cleaned and standardized initial input dataframe.
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
        .str.extract(r"(\d+)", expand=False)  # take first group of digits
    )
    # Convert to integer; rows without digits become NA
    df["Reaction"] = pd.to_numeric(rxn_num, errors="coerce").astype("Int64")

    return df


def parse_input_file(file_path_or_df: Union[str, Path, pd.DataFrame],
                     save_as_csv: bool = False):
    """
    Clean and standardize a initial input file

    The initial input file can be provided as a path to a file or a dataframe.

    Parameters
    ----------
    file_path_or_df : Union[str, Path, pd.DataFrame]
        The path to the initial input file or a dataframe.
    save_as_csv : bool, optional
        Whether to save the dataframe as a csv file. Default is False.
        For testing purposes.

    Returns
    -------
    df : pd.DataFrame
        The cleaned and standardized initial input dataframe.
    """

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
    df = pd.read_excel(path, engine="openpyxl")
    df = _normalize_cat_loading_df(df)
    if save_as_csv:
        out = path.with_suffix(".csv")
        df.to_csv(out, index=False)
    return df


def timepoint_map(df):
    """
    Map the timepoints to a dictionary.

    Parameters
    ----------
    df : pd.DataFrame
        The initial input dataframe.
    Returns
    -------
    timepoint_map : dict
        A dictionary mapping the timepoints to a dictionary.
    """
    time_df = df["time"].dropna()
    timepoint_map = dict(enumerate(time_df.astype(str).tolist()))
    return timepoint_map


def num_reactions(df):
    """
    Get the number of reactions in the initial input dataframe.

    Parameters
    ----------
    df : pd.DataFrame
        The initial input dataframe.
    Returns
    -------
    num_reactions : int
        The number of reactions in the initial input dataframe.
    """
    return df['Reaction'].nunique()
