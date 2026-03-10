"""
Add information from the initial input file to the dataframe.
This includes the time and reaction columns.
Any other columns from the initial input file are added as well.
They'll be visible in the plot as the user hovers over the data points.
"""
import pandas as pd
from src.parsing import parsing_initial_input


def _add_time_and_rxn(df, cat_df, save_as_csv=False):
    """
    Add Time and Reaction to the dataframe.

    Parameters
    -----------
    df : pd.DataFrame
        The cleaned up HPLC data dataframe to add the time and reaction to.
    cat_df : pd.DataFrame
        The cleaned up catalyst loading dataframe.
    save_as_csv : bool, optional
        Whether to save the dataframe as a csv file. Default is False.
        For testing purposes.

    Returns
    -------
    df : pd.DataFrame
        HPLC  dataframe with the time and reaction added.
    """

    # Get the number of reactions and the timepoint map
    num_of_reactions = parsing_initial_input.num_reactions(cat_df)
    timepoint_map = parsing_initial_input.timepoint_map(cat_df)

    # Add the reaction and time columns to the dataframe
    df["Reaction"] = (df.index % num_of_reactions) + 1

    df["Timepoint_Number"] = df.index // num_of_reactions
    df["Time"] = df["Timepoint_Number"].map(timepoint_map)
    # Convert the time column to a float
    df["Time"] = df["Time"].astype(float)
    # Drop the timepoint number column
    df = df.drop(columns=["Timepoint_Number"], errors="ignore")

    if save_as_csv:
        df.to_csv("time_and_rxn.csv", index=False)

    return df


def _add_other_info(df, cat_df, save_as_csv: bool = False):
    """
    Merge any reaction conditions from the initial input file to the dataframe.
    Done after time and reaction are added to the dataframe.

    Parameters
    -----------
    df : pd.DataFrame
        The cleaned up HPLC data dataframe to add initial input conditions to.
    cat_df : pd.DataFrame
        The cleaned up initial input loading dataframe.
    save_as_csv : bool, optional
        Whether to save the dataframe as a csv file. Default is False.
        For testing purposes.

    Returns
    -------
    df : pd.DataFrame
        HPLC dataframe with the initial input conditions added.
    """
    merged = df.copy()
    lookup_copy = cat_df.copy()
    lookup_copy = lookup_copy.drop(columns=["time", "well"], errors="ignore")

    # One row per reaction so merge is many-to-one
    lookup_copy = cat_df.drop_duplicates(subset=["Reaction"], keep="first")

    merged = pd.merge(merged, lookup_copy, on="Reaction", how="left")

    if save_as_csv:
        merged.to_csv("merged_data.csv", index=False)
    return merged


def add_loading_data_info(df, cat_df, save_as_csv: bool = False):
    """
    Add the time and reaction columns and any other information from
    the initial input file to the HPLC data.

    Parameters
    -----------
    df : pd.DataFrame
        The cleaned up HPLC data dataframe to add the time and reaction to.
    cat_df : pd.DataFrame
        The cleaned up initial input loading dataframe.
    save_as_csv : bool, optional
        Whether to save the dataframe as a csv file. Default is False.
        For testing purposes.

    Returns
    -------
    df : pd.DataFrame
        HPLC dataframe with the time and reaction and other information added.
    """
    df = _add_time_and_rxn(df, cat_df, save_as_csv)
    df = _add_other_info(df, cat_df, save_as_csv)
    return df
