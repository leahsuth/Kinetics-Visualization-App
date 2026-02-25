# THIS WILL BE TO PARSE THE CAT LOADING FILES INTO A DATAFRAME
import pandas as pd
from pathlib import Path
import openpyxl  # needed for excel file -> df


def parse_cat_loading_file(file_path, save_as_csv=False):
    df = pd.read_excel(file_path)
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
    df.columns = df.columns.str.strip()
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
            new_cols[c] = "reaction"
        if "well" in c.lower():
            new_cols[c] = "well"
    df = df.rename(columns=new_cols)
    if save_as_csv:
        df.to_csv(file_path.replace(".xlsx", ".csv"), index=False)
    return df


def row_or_column(df):
    """
    Return 'row' if wells are A1,A2,A3 (same column letter);
    Return 'column' if A1,B1,C1 (same row number).
    """

    wells = df["well"].astype(str).str.strip()
    parts = wells.str.extract(r"^([A-Za-z]+)(\d+)$", expand=True)

    letters = parts[0]
    numbers = parts[1].astype(int)

    # Take first 3 wells to determine layout
    # If letter is the same -> row layout
    # If number is the same -> column layout
    n = min(3, len(df))
    first_letters = letters.iloc[:n]
    first_numbers = numbers.iloc[:n]
    if first_letters.nunique() == 1:
        return "row"
    if first_numbers.nunique() == 1:
        return "column"

    # IF NEEDED: If the variance of letters is greater, it's column
    # layout, otherwise it's row layout
    if letters.nunique() <= numbers.nunique():
        return "row"
    return "column"


def num_timepoints(df):
    return df['time'].nunique()


def num_reactions(df):
    return df['reaction'].nunique()


def cols_per_timepoint(df):
    col_num = (
        df["well"].astype(str).str.extract(r"(\d+)$", expand=False)
        .dropna()
        .astype(int)
    )
    if len(col_num) == 0:
        raise ValueError(
            "No well labels matched pattern (digits at end). "
            "Check that the 'well' column contains values like A1, B12, etc."
        )
    return int(col_num.max())


if __name__ == "__main__":
    df_excel = parse_cat_loading_file(
        "./data/NB-0123-0005_Cat_Loading_Conditions.xlsx", True
    )

    print(num_timepoints(df_excel))
    print(num_reactions(df_excel))
    print(cols_per_timepoint(df_excel))
