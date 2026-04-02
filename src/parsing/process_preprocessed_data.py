import pandas as pd

from src.parsing.parse_file_type import read_input


def _add_reaction_by_time_resets(df):
    """
    Add Reaction column: 1 until time decreases vs the previous row, then 2, etc.
    Rows with equal or increasing time stay in the same reaction.
    """
    if df.empty or "time" not in df.columns:
        return df
    t = pd.to_numeric(df["time"], errors="coerce")
    time_decreased = t.shift(1).notna() & t.notna() & (t < t.shift(1))
    out = df.copy()
    out["Reaction"] = time_decreased.cumsum() + 1
    return out


def process_preprocessed_data(file_name, save_as_csv=False):
    """
    Process a preprocessed data file into a pandas dataframe

    Parameters
    ----------
    file_name : str, Path, or file-like
        Path to file or Streamlit UploadedFile (must have .name for extension)
    save_as_csv : bool
        Saves as CSV if True
        For testing purposes.

    Returns
    -------
    df : pandas dataframe
        The processed preprocessed data dataframe
    """
    df = read_input(file_name)
    cols = list(df.columns)
    # change name of first column to Sample Name
    if cols:
        cols[0] = "Sample Name"
        df.columns = cols
    df.columns = [str(c).strip() for c in df.columns]
    # need to change "Time" "time" or "timepoint" to "time"
    df.rename(columns={"Time": "time", "time": "time", "timepoint": "time"}, inplace=True)
    df = _add_reaction_by_time_resets(df)
    if save_as_csv:
        df.to_csv(file_name.name + ".csv", index=False)
    return df
