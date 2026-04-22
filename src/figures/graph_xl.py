import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

symbol_seq = ["circle","square","diamond","cross","x","triangle-up","triangle-down","triangle-left","triangle-right","pentagon",
    "hexagon","star","hourglass","bowtie"]

# ----Helper Functions For Titles----------------------------------------


def update_measurement_label(measure_col: str):
    """
    Update the measurement label to be more readable.
    """
    measurement_labels = {
        "peak_area": "Peak Area",
        "peak_ap": "Peak AP",
    }
    if measure_col in measurement_labels:
        return measurement_labels[measure_col]
    # Fallback: best-effort title case.
    return measure_col.replace("_", " ").title()


def update_reaction_suffix(df: pd.DataFrame):
    """
    Update the reaction suffix to include all reactions.
    """
    if "reaction" not in df.columns:
        raise ValueError("reaction not in dataframe")
    reactions = (
        df["reaction"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )
    if not reactions:
        return None
    reactions = sorted(reactions, key=lambda x: (len(x), x))
    if len(reactions) == 1:
        return f"Reaction {reactions[0]}"
    return f"Reactions {', '.join(reactions)}"


# ----Graph from XLSX----------------------------------------


def graph_from_xlsx(
    df: pd.DataFrame,
    select_meas: str,
    color_select: str,
    chart_type: str,
    title_suffix: str | None = None,
    time_unit: str = "hours",
) -> go.Figure:
    """
    Build Plotly figure from a given dataframe.
    """
    # Ensure the color dimension is treated as categorical so we always get
    # discrete colors
    if color_select in df.columns:
        df = df.copy()
        df[color_select] = df[color_select].astype(str)

    df = df.sort_values(by=["reaction", "reactant", "time"])
    # Keep line traces separated by chemistry series; without this, Plotly can
    # connect points across different reactants when using shared colors.
    if {"reaction", "reactant"}.issubset(df.columns):
        df = df.copy()
        df["_series_group"] = (
            df["reaction"].astype(str) + " | " + df["reactant"].astype(str)
        )
    else:
        df["_series_group"] = df.index.astype(str)

    hover_data = {c: True for c in df.columns}

    fig_kwargs = dict(
        width=1200,
        height=500,
    )

    # Use a palette with clearly separated colors.
    qualitative_colors = px.colors.sequential.Viridis

    pretty_meas = update_measurement_label(select_meas)

    if chart_type == "Line":
        fig = px.line(
            df,
            x="time",
            y=select_meas,
            color=color_select,
            symbol="reactant",
            symbol_sequence=symbol_seq,
            line_group="_series_group",
            hover_data=hover_data,
            color_discrete_sequence=qualitative_colors,
            markers=True,
            **fig_kwargs,
        )
    else:
        fig = px.scatter(
            df,
            x="time",
            y=select_meas,
            color=color_select,
            symbol="reactant",
            symbol_sequence=symbol_seq,
            hover_data=hover_data,
            color_discrete_sequence=qualitative_colors,
            **fig_kwargs,
        )
        fig.update_traces(marker=dict(size=10))

    suffix = title_suffix or update_reaction_suffix(df)
    title_text = f"{pretty_meas} vs. Time"
    if suffix:
        title_text = f"{title_text} for {suffix}"

    fig.update_layout(
        title=dict(
            text=title_text,
            font=dict(size=28),
            x=0.5,
            xanchor="center",
            y=0.95,
            yanchor="top",
        )
    )

    fig.update_xaxes(title_text=f"Time ({time_unit})")
    fig.update_yaxes(title_text=pretty_meas)
    return fig
