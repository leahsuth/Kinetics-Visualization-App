import pandas as pd
import streamlit as st


def plot_process(
    df: pd.DataFrame,
    selected_reactions: list,
    selected_analytes: list,
):
    """
    Filter and normalize plotting data, then select a measurement column.

    Args
    ------
    df : Input dataframe containing reactant, time, and measurement columns.
    selected_reactions : Currently unused reaction filter selections.
    selected_analytes : Reactants to keep in the returned dataframe.

    Returns
    -------
    df : Filtered dataframe with numeric `time` and selected measurement values.
    select_meas : Selected measurement column name from Streamlit (`peak_area` or `peak_ap`).

    Raises
    ------
    ValueError: If neither `peak_area` nor `peak_ap` exists in the dataframe.
    """
    df = df[df["reactant"].astype(str).isin(selected_analytes)]
    df = df[df["reactant"].isin(selected_analytes)]

    # Coerce time to numeric so sorting/Plotly x-axis is correct even if time is a string.
    if "time" in df.columns:
        df["time"] = pd.to_numeric(df["time"], errors="coerce")
    elif "Time" in df.columns:
        # Defensive: if upstream produced capitalized Time, normalize to lowercase.
        df = df.rename(columns={"Time": "time"})
        df["time"] = pd.to_numeric(df["time"], errors="coerce")

    preferred = ["peak_area", "peak_ap"]
    measurement_cols = [c for c in preferred if c in df.columns]

    if not measurement_cols:
        raise ValueError("No peak_area or peak_ap columns found in dataframe.")

    measurement_labels = {
        "peak_area": "Peak Area",
        "peak_ap": "Peak AP",
    }

    select_meas = st.selectbox(
        "Select measurement to plot",
        options=measurement_cols,
        format_func=lambda x: measurement_labels.get(x, x),
    )

    df[select_meas] = pd.to_numeric(df[select_meas], errors="coerce")
    df = df.dropna(subset=["time", select_meas])

    return df, select_meas
