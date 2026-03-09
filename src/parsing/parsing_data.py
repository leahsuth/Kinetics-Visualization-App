"""
Parse kinetics data from CSV and Excel (ChemStation) files.
Excel support requires openpyxl (for .xlsx) and xlrd (for .xls).
"""

from src.parsing.parsing_initial_input import parse_input_file
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
    first_line : str
    """
    first_line = process_first_line(hplc_data)
    df = process_data(hplc_data)
    df = add_loading_data_info(df, cat_df)
    df = standardize_data(df)
    return df, first_line


def process_manual(cat_loading_path: str, data_path: str, save_as_csv):
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
    df_cat = parse_input_file(cat_loading_path, save_as_csv)
    df = process_data(data_path, save_as_csv)
    df = add_loading_data_info(df, df_cat, save_as_csv)
    df = standardize_data(df, save_as_csv)
    return df


if __name__ == "__main__":
    process_manual()
