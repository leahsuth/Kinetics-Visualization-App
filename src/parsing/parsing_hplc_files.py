"""
Parse .csv, .xlsx, and .xls files into pandas DataFrames.
Extract the first line/row for description/metadata.
"""

import pandas as pd
from pathlib import Path
from src.parsing.parse_file_type import read_input



def process_first_line(file_name):
    """
    Extract the first row/line of a file for description/metadata.
    Handles CSV (text) and Excel (.xlsx, .xls) files.

    Parameters
    ----------
    file_name : str, Path, or file-like
        Path to file or a file-like object (e.g. Streamlit UploadedFile with a
        .name attribute).
    """
    # Normalize to get an extension while preserving the original object
    if isinstance(file_name, (str, Path)):
        filepath = Path(file_name)
        ext = filepath.suffix.lower()
        file_obj = file_name
    else:
        fname = getattr(file_name, "name", None)
        filepath = Path(fname) if fname else Path("data.xlsx")
        ext = filepath.suffix.lower()
        file_obj = file_name

    if ext == ".csv":
        # For real paths, just open the file
        if isinstance(file_obj, (str, Path)):
            with open(file_obj, "r", encoding="utf-8") as f:
                return f.readline()
        # For file-like objects, read the first line from the stream
        try:
            file_obj.seek(0)
        except Exception:
            pass
        first_line = file_obj.readline()
        if isinstance(first_line, bytes):
            first_line = first_line.decode("utf-8", errors="ignore")
        return first_line

    if ext in (".xlsx", ".xls"):
        engine = "openpyxl" if ext == ".xlsx" else "xlrd"
        # Both paths and file-like objects are supported by pandas.read_excel
        try:
            file_obj.seek(0)
        except Exception:
            pass
        df = pd.read_excel(
            file_obj, sheet_name=0, header=None, nrows=1, engine=engine
        )
        return df.iloc[0].astype(str).str.cat(sep=", ")

    raise ValueError(f"Unsupported file type: {ext}")


def process_data(file_name, save_as_csv=False):
    """
    Process .xlsx, .xls, and .csv files into Pandas Dataframe

    This works for both filesystem paths and file-like objects (e.g.
    Streamlit UploadedFile) and for Excel files with multiple sheets.

    Parameters
    -----------
    file_name : str, Path, or file-like
        Path to file or Streamlit UploadedFile (must have .name for extension)
    save_as_csv : bool
        Saves as CSV if True
        For testing purposes.

    Returns
    --------
    df : pandas dataframe
        Dataframe with data from provided file
    """

    # Handle both file paths and uploaded files
    if isinstance(file_name, (str, Path)):
        filepath = Path(file_name)
    else:
        fname = getattr(file_name, "name", None)
        if not fname:
            raise TypeError(
                "file_name must have a .name attribute"
            )
        filepath = Path(fname)

    ext = filepath.suffix.lower()
    out_path = filepath.with_suffix(".csv")

    if ext == ".csv":
        return process_csv(file_name, out_path, save_as_csv)

    elif ext in (".xlsx", ".xls"):
        engine = "openpyxl" if ext == ".xlsx" else "xlrd"
        return process_excel(file_name, out_path, engine, save_as_csv)
    else:
        raise ValueError(
            f"Must be a CSV or Excel filetype. Unsupported file type: {ext}"
        )


def process_csv(file_name, out_path, save_as_csv=False):
    """
    Process a CSV file into a pandas dataframe
    THIS ONLY HANDLES THE MOCK DATA
    #TODO: Ask sponsor if this is required?
    """
    # Reuse centralized file-type reader for consistency across parsing modules.
    df = read_input(file_name)
    cols = list(df.columns)
    # change name of first column to Sample Name
    cols[0] = "Sample Name"
    df.columns = cols
    df.columns = df.columns.str.strip()
    if save_as_csv:
        df.to_csv(out_path, index=False)
    return df


def process_excel(file_name, out_path, engine, save_as_csv=False):
    """
    Process an Excel file into a pandas dataframe

    Parameters
    -----------
    file_name : str, Path, or file-like
        Path to file or Streamlit UploadedFile (must have .name for extension)
    out_path : str, Path
        Path to save the dataframe as a csv file
    engine : str
        The engine to use to read the excel file
    save_as_csv : bool
        Saves as CSV if True
        For testing purposes.

    Returns
    --------
    df : pandas dataframe
        Dataframe with data from provided file
    """
    # read data into basic dataframe
    raw = pd.read_excel(
        file_name, header=None, engine=engine
        )
    # find the first row that contains "Peak RT"
    matches = raw.index[
        raw.apply(
            lambda r: r.astype(str).str.contains("Peak RT", na=False).any(),
            axis=1,
        )
    ]

    # header row is the one with the RT, above the peak RT row
    hdr1_row = matches[0] - 1
    # Re-read sheet with multi-row header (RT, Peak Area/etc.)
    df = pd.read_excel(
        file_name,
        skiprows=int(hdr1_row),
        header=[0, 1],
        engine=engine,
    )
    level0 = df.columns.get_level_values(0)
    level1 = df.columns.get_level_values(1)
    # Extract the two header levels
    level0_filled = pd.Series(level0).ffill()
    # Rebuild the MultiIndex using level 0
    df.columns = pd.MultiIndex.from_arrays([level0_filled, level1])
    # Now flatten the MultiIndex into single-level column names.
    # Normalize retention-time headers to match expected analyte names.
    flat_columns = []
    for parent, child in df.columns:
        try:
            if isinstance(parent, (int, float)) or (isinstance(parent, str) and parent.replace(".", "", 1).replace("-", "", 1).isdigit()):
                parent = f"rt_{parent}"
        except (TypeError, ValueError):
            pass
        flat_columns.append(f"{parent}__{child}")
    df.columns = flat_columns

    # drop any rows or columns that are empty
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")

    # Standardize the column names
    cols = list(df.columns)
    cols[0] = "Sample_Name"
    cols[1] = "Well"
    cols[2] = "Injection_Number"
    df.columns = cols

    # Delete unnecessary column, well
    df = df.drop(columns="Well")

    # Process injection data
    # See if there are duplicate Sample Names
    if df["Sample_Name"].duplicated().any():
        # Sort by Sample Name and Injection Number
        df.sort_values(by=["Sample_Name", "Injection_Number"], inplace=True)
        # Drop duplicate Sample Names by keeping the last one
        df.drop_duplicates(subset=["Sample_Name"], keep="last", inplace=True)

    # get rid of injection number column
    df = df.drop(columns="Injection_Number")

    # Add a sample_Number column
    df["Sample_Number"] = pd.to_numeric(
        df["Sample_Name"].str.extract(r"-([^-]+)$")[0]).astype("Int64")

    if save_as_csv:
        df.to_csv(out_path, index=False)
    return df
