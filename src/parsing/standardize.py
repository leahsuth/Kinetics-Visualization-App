"""
Standardize the data into a long format.
"""

import pandas as pd


def standardize_data(df, save_as_csv=False):
    """
    Standardize the data into a long format.

    Each row is a single measurement for one substance
    at a given time for a specific reaction.

    Parameters
    ----------
    df : pandas dataframe
      Dataframe with HPLC data after time and reaction are added.
    save_as_csv : bool
      Saves as CSV if True
      For testing purposes.

    Returns
    -------
    df : pandas dataframe
      Dataframe with standardized data
    """
    # TODO: Need to check if this is needed
    # Deduplicate columns by lowercased name (keep first).
    # After merge we can have both "Reaction" and "reaction";
    seen_lower = {}
    dedup_cols = []
    for c in df.columns:
        cl = str(c).lower()
        if cl not in seen_lower:
            seen_lower[cl] = c
            dedup_cols.append(c)
    df = df[dedup_cols].copy()

    # Id columns = everything that is not a measurement column
    # Measurement columns follow "Reactant__Suffix" patern
    id_cols = [c for c in df.columns if "__" not in str(c)]
    value_cols = [c for c in df.columns if "__" in str(c)]

    # Pivot/groupby drops rows where any grouping key is NA. Many condition
    # columns (e.g., role/ligand/catalyst) are optional and frequently blank,
    # so fill object-id NAs with an empty string to preserve rows.
    obj_id_cols = [c for c in id_cols if df[c].dtype == object]
    if obj_id_cols:
        df[obj_id_cols] = df[obj_id_cols].fillna("")

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

    # Use everything before "__" as the Reactant identifier
    # (e.g. "RT_3__Peak Area" -> "RT_3").
    reactant_col = (
        melted_data["Measurement"].astype(str).str.extract(
            r"^(.*?)__", expand=False)
    )
    melted_data.insert(len(id_cols), "Reactant", reactant_col)

    # remove the "__" from the measurement column
    # (e.g. "Peak Area")
    melted_data["Measurement"] = melted_data["Measurement"].str.replace(
        r"^.*?__", "", regex=True
    )

    # Pivot the data to a wide format.
    # Handles duplicate index/column pairs.
    pivot_index = id_cols + ["Reactant"]
    piv_data = melted_data.pivot_table(
        index=pivot_index, columns="Measurement", values="Value"
    ).reset_index()

    # sort the data by Reaction, Time
    piv_data = piv_data.sort_values(by=["Reaction", "Time"])

    # Standardize the column names
    columns_list = list(piv_data.columns)
    for i, c in enumerate(columns_list):
        columns_list[i] = str(c).lower().replace(" ", "_")
    piv_data.columns = columns_list

    # Drop peak rt column (not needed), added errors="ignore" to avoid errors 
    # if the column doesn't exist
    piv_data = piv_data.drop(columns=["peak_rt"], errors="ignore")

    if save_as_csv:
        piv_data.to_csv("final_data.csv", index=False)
    return piv_data
