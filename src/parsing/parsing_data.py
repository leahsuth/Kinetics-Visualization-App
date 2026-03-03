"""
Parse kinetics data from CSV and Excel (ChemStation) files.
Excel support requires openpyxl (for .xlsx) and xlrd (for .xls).
"""

import re
import pandas as pd
from pathlib import Path
from typing import Optional

import openpyxl  # needed for excel file -> df
from src.parsing import parsing_initial_input


def process_first_line(file_name):
    """
    Extract the first row/line of a file for description/metadata.
    Handles CSV (text) and Excel (.xlsx, .xls) files.

    Parameters
    ----------
    file_name : str, Path, or file-like
        Path to file or a file-like object (e.g. Streamlit UploadedFile with a
        .name attribute). For file-like objects we reset the stream position
        before reading.
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
    Processing .xlsx, .xls, and .csv files into Pandas Dataframe

    This works for both filesystem paths and file-like objects (e.g.
    Streamlit UploadedFile) and for Excel files with multiple sheets.

    Parameters
    -----------
    file_name : str, Path, or file-like
        Path to file or Streamlit UploadedFile (must have .name for extension)
    save_as_csv : bool
        Saves as CSV if True
        This is mainly for testing purposes.
        No need to save as CSV for production.

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
                "file_name must be a path or a file-like object with a .name attribute"
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

    This only handles the mock data for now.
    Need to ask if this requires additional functionality.
    """
    df = pd.read_csv(file_name)
    cols = list(df.columns)
    # change name of first column to Sample Name
    cols[0] = "Sample Name"
    df.columns = cols
    if save_as_csv:
        df.to_csv(out_path, index=False)
    return df


def process_excel(file_name, out_path, engine, save_as_csv=False):
    """
    Process an Excel file into a pandas dataframe
    """
    xls = pd.ExcelFile(file_name, engine=engine)
    num_sheets = len(xls.sheet_names)

    parsed = []  # store all of the df from each Excel sheet

    # process all of the sheet
    for i in range(num_sheets):
        parsed.append(process_excel_sheet(file_name, i, engine))

    merged_df = pd.concat(parsed, ignore_index=True)
    if save_as_csv:
        merged_df.to_csv(out_path, index=False)
    return merged_df


def process_excel_sheet(file_name, sheet_number, engine):
    """
    Process an Excel sheet into a pandas dataframe
    """
    # read data into basic dataframe
    raw = pd.read_excel(
        file_name, sheet_name=sheet_number, header=None, engine=engine
        )
    # find the first row that contains "Peak RT"
    matches = raw.index[
        raw.apply(
            lambda r: r.astype(str).str.contains("Peak RT", na=False).any(),
            axis=1,
        )
    ]

    if len(matches) == 0:
        raise ValueError(f"No 'Peak RT' found in sheet {sheet_number}")

    # header row is the one with the RT, above the peak RT row
    hdr1_row = matches[0] - 1
    # Re-read sheet with multi-row header (RT, Peak Area/etc.)
    df = pd.read_excel(
        file_name,
        sheet_name=sheet_number,
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
    # Now flatten the MultiIndex into single-level column names
    flat_columns = []
    for parent, child in df.columns:
        flat_columns.append(f"{parent}__{child}")
    df.columns = flat_columns

    # drop any rows or columns that are empty
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")

    # Standardize the column names
    cols = list(df.columns)
    cols[0] = "Reaction"
    cols[1] = "Well"
    cols[2] = "Injection_Numbers"
    df.columns = cols

    # Create a new column for Plate Number, defaults to AAA
    new_col = (
        df["Well"]
        .where(df["Well"].str.contains("-"), "AAA")
        .str.split("-")
        .str[0]
    )
    df.insert(1, "Plate_Number", new_col)

    # Remove Plate_Number- from Well if it exists
    df["Well"] = df["Well"].str.replace(r"^.*?-", "", regex=True)

    # Add the sheet number to the dataframe
    df["Sheet_Number"] = sheet_number

    # Adding a unique well ID to the dataframe
    df["Unique_Well_ID"] = (df.index // 96).astype(str) + df["Well"].astype(str)

    return df


def _parse_well_labels(well_series):
    """
    Parse well labels into components suitable for sorting.

    Returns a dataframe with integer columns:
      - repeat well: repeat well indices (0 if omitted in the label)
      - row_idx: 0-based row index (A->0, ..., H->7)
      - col: numeric column index
    """
    s = well_series.astype(str)

    # Optional leading digits for repeat well, then a row letter A–H, then column digits.
    extracted = s.str.extract(r"^(\d*)([A-H])(\d+)$")
    extracted.columns = ["repeat_well", "row", "col"]

    # Treat missing repeats as 0
    extracted["repeat_well"] = (
        extracted["repeat_well"].replace({"": "0"}).fillna("0").astype(int)
    )

    row_map = {c: i for i, c in enumerate("ABCDEFGH")}
    extracted["row_idx"] = extracted["row"].map(row_map)
    extracted["col"] = extracted["col"].astype(int)

    return extracted[["repeat_well", "row_idx", "col"]]


def sort_wells_by_time_blocks(df, cat_df, save_as_csv=False):
    """
    Sort a dataframe of wells using the unique wells

    Parameters
    ----------
    df : pandas.DataFrame
        Dataframe containing a well identifier column.
    cat_df : pandas.DataFrame
        Catalyst-loading dataframe used to determine cols_per_timepoint.
    """
    cols_per_timepoint = parsing_initial_input.cols_per_timepoint(cat_df)

    parsed = _parse_well_labels(df["Unique_Well_ID"])

    parsed["block"] = (parsed["col"] - 1) // cols_per_timepoint
    parsed["rep"] = (parsed["col"] - 1) % cols_per_timepoint

    tmp = df.assign(
        _repeat_well=parsed["repeat_well"].values,
        _row_idx=parsed["row_idx"].values,
        _block=parsed["block"].values,
        _rep=parsed["rep"].values,
    )

    sorted_df = (
        tmp.sort_values(by=["_repeat_well", "_block", "_row_idx", "_rep"])
        .drop(columns=["_repeat_well", "_row_idx", "_block", "_rep"])
        .reset_index(drop=True)
    )

    if save_as_csv:
        sorted_df.to_csv("sorted_wells.csv", index=False)

    return sorted_df


def time_and_rxn(df, cat_df, save_as_csv=False):
    timepoint_map = parsing_initial_input.timepoint_map(cat_df)
    num_time_blocks = max(len(timepoint_map), 1)
    # Use the larger of: data-derived count, or setup-derived count.
    # So we never collapse to 1 reaction when the setup only lists the one you edited.
    from_data = len(df) // num_time_blocks
    from_setup = parsing_initial_input.num_reactions(cat_df) or 0
    num_of_reactions = max(from_data, from_setup)
    if num_of_reactions <= 0:
        num_of_reactions = 1
    # Time = time block (0, 1, 2, ...); Reaction = 1..num_of_reactions within each block
    df["Time_Index"] = df.index // num_of_reactions
    df["Reaction"] = (df.index % num_of_reactions) + 1

    df["Time"] = df["Time_Index"].map(timepoint_map)
    df["Time"] = pd.to_numeric(df["Time"], errors="coerce")

    if save_as_csv:
        df.to_csv("time_and_rxn.csv", index=False)

    return df


def add_initial_input_conditions(df: pd.DataFrame, lookup_df: Optional[pd.DataFrame], save_as_csv: bool = False):
    """
    Add any extra conditions from the initial input file to the dataframe.
    Keeps one row per reaction from the lookup so the merge is many-to-one and
    we don't blow up rows or add duplicate time columns that break standardize_data.
    """
    merged = df.copy()
    lookup_copy = lookup_df.copy()
    lookup_copy = lookup_copy.drop(columns=["time", "well"], errors="ignore")
    # One row per reaction so merge is many-to-one (no row explosion, no duplicate time col)
    lookup_copy = lookup_copy.drop_duplicates(subset=["Reaction"], keep="first")

    merged = pd.merge(merged, lookup_copy, on="Reaction", how="left")

    if save_as_csv:
        merged.to_csv("merged_data.csv", index=False)
    return merged


def standardize_data(df, save_as_csv=False):
    """
    Standardize the data into a long format.

    Only columns whose names contain "__" (ChemStation-style measurement names,
    e.g. "RT_3__Peak Area") are melted. All other columns are kept as id columns,
    so user-added note columns are preserved and not melted.

    Parameters
    ----------
    df : pandas dataframe
      Dataframe with data from provided file
    save_as_csv : bool
      Saves as CSV if True
      This is mainly for testing purposes.
      No need to save as CSV for production.

    Returns
    -------
    df : pandas dataframe
      Dataframe with standardized data
    """
    # Deduplicate columns by lowercased name (keep first). After merge we can have
    # both "Reaction" and "reaction"; pivot then collapses 32 reactions to 1.
    seen_lower = {}
    dedup_cols = []
    for c in df.columns:
        cl = str(c).lower()
        if cl not in seen_lower:
            seen_lower[cl] = c
            dedup_cols.append(c)
    df = df[dedup_cols].copy()

    # Id columns = everything that is not a measurement column.
    # Measurement columns follow "Reactant__Suffix" (e.g. "Product__Peak Area").
    id_cols = [c for c in df.columns if "__" not in str(c)]
    value_cols = [c for c in df.columns if "__" in str(c)]

    if not value_cols:
        raise ValueError(
            "No measurement columns (with '__') found. Cannot standardize."
        )

    # melt the data into a long format
    melted_data = pd.melt(
        df,
        id_vars=id_cols,
        value_vars=value_cols,
        var_name="Measurement",
        value_name="Value",
    )

    # Use everything before "__" as the Reactant identifier (e.g. "RT_3__Peak Area" -> "RT_3").
    reactant_col = (
        melted_data["Measurement"]
        .astype(str)
        .str.extract(r"^(.*?)__", expand=False)
    )
    melted_data.insert(len(id_cols), "Reactant", reactant_col)

    # remove the "__" from the measurement column so it only contains the suffix (e.g. "Peak Area")
    melted_data["Measurement"] = melted_data["Measurement"].str.replace(
        r"^.*?__", "", regex=True
    )

    # pivot_table handles duplicate index/column pairs
    pivot_index = id_cols + ["Reactant"]
    pivoted_data = melted_data.pivot_table(
        index=pivot_index, columns="Measurement", values="Value"
    ).reset_index()

    # sort the data by Reaction
    pivoted_data = pivoted_data.sort_values(by=["Reaction", "Time"])
    # Drop internal/plate columns
    drop_candidates = [
        "Time_Index", "Injection_Numbers", "Sheet_Number", "Unique_Well_ID",
        "Well", "Plate_Number", "peak_rt"
    ]
    pivoted_data = pivoted_data.drop(
        columns=[c for c in drop_candidates if c in pivoted_data.columns],
        errors="ignore",
    )

    columns_list = list(pivoted_data.columns)
    for i, c in enumerate(columns_list):
        columns_list[i] = str(c).lower().replace(" ", "_")
    pivoted_data.columns = columns_list

    if save_as_csv:
        pivoted_data.to_csv("final_data.csv", index=False)
    return pivoted_data


def standardize_data_realdata(df, save_as_csv=False):
    # Backwards-compatible name expected by tests and callers.
    return standardize_data(df, save_as_csv=save_as_csv)


def process_manual(
    data_path: str = "./data/NB-0123-0003_Impurity_Study_Data.xlsx",
    cat_loading_path: str = "./data/NB-0123-0003_Impurity_Study_Conditions.xlsx",
):
    """
    Replicate the Streamlit Excel-processing pipeline on the command line.

    Steps (each saved to CSV):
      1. process_data -> base CSV of the kinetics data
      2. parse_cat_loading_file -> cleaned catalyst-loading conditions
      3. sort_wells_by_time_blocks -> sorted_wells.csv
      4. time_and_rxn -> time_and_rxn.csv
      5. standardize_data -> final_data.csv
      6. merge standardized data with cat-loading lookup (one row per Reaction)
         -> final_with_conditions.csv
    """
    # 1) Raw Excel -> dataframe (and CSV)
    df_excel = process_data(data_path, save_as_csv=True)

    # 2) Catalyst loading / experiment setup
    df_cat = parsing_initial_input.parse_cat_loading_file(
        cat_loading_path
    )

    # 3) Sort wells into time blocks
    df_sorted = sort_wells_by_time_blocks(df_excel, df_cat, save_as_csv=True)

    # 4) Add Time and Reaction indices
    df_time_and_rxn = time_and_rxn(df_sorted, df_cat, save_as_csv=True)

    # 5) Standardize into long-format, one row per reaction/measurement
    final_df = standardize_data(df_time_and_rxn, save_as_csv=True)

    # 6) Merge annotations/conditions from the cat-loading file,
    #    mirroring the Streamlit logic in pages/Kinetics.py
    lookup = df_cat.drop_duplicates(subset=["Reaction"], keep="first").drop(
        columns=["time", "well"], errors="ignore"
    )
    final_with_conditions = final_df.merge(
        lookup, left_on="reaction", right_on="Reaction", how="left"
    )
    if (
        "Reaction" in final_with_conditions.columns
        and "reaction" in final_with_conditions.columns
    ):
        final_with_conditions = final_with_conditions.drop(
            columns=["Reaction"], errors="ignore"
        )

    final_with_conditions.to_csv("final_with_conditions.csv", index=False)
    return final_with_conditions


if __name__ == "__main__":
    process_manual()
