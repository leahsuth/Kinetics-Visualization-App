"""
Parse kinetics data from CSV and Excel (ChemStation) files.
Excel support requires openpyxl (for .xlsx) and xlrd (for .xls).
"""

from src.parsing.parsing_cat_loading_conditions import parse_conditions_df
from src.parsing.add_loading_data_info import add_loading_data_info
from src.parsing.standardize import standardize_data
from src.parsing.parsing_hplc_files import process_first_line, process_data


def process_streamlit(cat_df, hplc_data):
    """
    Process the data for streamlit usage.

    Parameters
    ----------
    cat_loading_path : str
        The path to the initial input file.
        This dataframe should already have been standardized.
    data_path : str
        The path to the HPLC data file.
    save_as_csv : bool
        Whether to save the dataframes as CSV files.
    Returns
    -------
    df_standardized : pd.DataFrame
        The standardized HPLC data dataframe.
    df_after_add_loading : pd.DataFrame
        Data for download on Streamlit app
    first_line : str
    """
    first_line = process_first_line(hplc_data)
    df = process_data(hplc_data)
    df = add_loading_data_info(df, cat_df)
    df_after_add_loading = df.copy()
    df = standardize_data(df)
    return df, df_after_add_loading, first_line


def process_manual(cat_loading_path: str, data_path: str, save_as_csv=True):
    """
    Replicate the Streamlit Excel-processing pipeline on the command line.

    This can be for CLI usage. This works by:
    1. Parsing the initial input file
    2. Processing the HPLC data file
    3. Adding the time and reaction to the HPLC data
    4. Add any provided experimental conditions
    5. Standardizing the data so each row is a single measurement
    6. Returning the standardized data

    Parameters
    ----------
    cat_loading_path : str
        The path to the initial input file.
    data_path : str
        The path to the HPLC data file.
    save_as_csv : bool
        Whether to save the dataframes as CSV files.
    Returns
    -------
    df_standardized : pd.DataFrame
        The standardized HPLC data dataframe.
    """
    df_cat = parse_conditions_df(cat_loading_path, save_as_csv)
    df = process_data(data_path, save_as_csv)
    df = add_loading_data_info(df, df_cat, save_as_csv)
    df = standardize_data(df, save_as_csv)
    return df


if __name__ == "__main__":
    """
    Run the manual parsing pipeline (cat loading + HPLC data).

    Example to type into terminal to run the script:
    python3 -m src.parsing.parsing_data
    --initial_input "data/NB-0123-0005_Cat_Loading_Conditions.xlsx"
    --hplc_data "data/NB-0123-0005_Cat_Loading_Data.xlsx"
    """
    import argparse
    parser = argparse.ArgumentParser(description=
                                     "Run the manual parsing pipeline")
    parser.add_argument("--initial_input",
                        required=True,
                        help="Path to the initial input file.")
    parser.add_argument("--hplc_data",
                        required=True,
                        help="Path to the HPLC data file.")
    args = parser.parse_args()
    process_manual(args.initial_input, args.hplc_data)
