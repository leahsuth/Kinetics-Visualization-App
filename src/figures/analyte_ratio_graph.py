import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure


def build_ratio_figure(
    df: pd.DataFrame,
    reaction_col: str,
    chart_type: str,
    time_unit: str = "hours",
    title_suffix: str | None = None,
    ratio_label: str = "Analyte Ratio",
) -> tuple[Figure | None, str | None]:
    """
    Build the Plotly figure for analyte ratio plotting (no Streamlit).
    Returns (figure, None) on success, or (None, error_message).
    """
    if df.empty:
        return None, "No ratio data available to plot."
    if "time" not in df.columns:
        return None, 'Ratio data must include a "time" column.'
    if "analyte_ratio" not in df.columns:
        return None, 'Ratio data must include an "analyte_ratio" column.'
    if reaction_col not in df.columns:
        return None, f'Ratio data must include a "{reaction_col}" column.'

    df = df.copy()
    df["time"] = pd.to_numeric(df["time"], errors="coerce")
    df["analyte_ratio"] = pd.to_numeric(df["analyte_ratio"], errors="coerce")
    df = df.dropna(subset=["time", "analyte_ratio"])

    df[reaction_col] = df[reaction_col].astype(str)
    # Match main kinetics: compare normalized label (independent of main page chart type).
    is_line = str(chart_type or "").strip().casefold() == "line"
    # Order points for connected line traces
    if is_line:
        df = df.sort_values([reaction_col, "time"])

    hover_data = {"time": True, "analyte_ratio": True, reaction_col: True}
    fig_kwargs = dict(width=1200, height=500, hover_data=hover_data)

    if is_line:
        fig = px.line(
            df,
            x="time",
            y="analyte_ratio",
            color=reaction_col,
            line_group=reaction_col,
            markers=True,
            color_discrete_sequence=px.colors.qualitative.Plotly,
            **fig_kwargs,
        )
    else:
        fig = px.scatter(
            df,
            x="time",
            y="analyte_ratio",
            color=reaction_col,
            color_discrete_sequence=px.colors.qualitative.Plotly,
            **fig_kwargs,
        )

    title_text = "Analyte Ratio vs. Time"
    if title_suffix:
        title_text = f"{title_text} for {title_suffix}"
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
    fig.update_yaxes(title_text=ratio_label)
    return fig, None


def build_ratio_df(
    df: pd.DataFrame,
    reaction_col: str,
    numerator: str,
    denominator: str,
) -> pd.DataFrame:
    ratio_df = df[["time", reaction_col, numerator, denominator]].copy()
    ratio_df[numerator] = pd.to_numeric(ratio_df[numerator], errors="coerce")
    ratio_df[denominator] = pd.to_numeric(ratio_df[denominator], errors="coerce")
    ratio_df = ratio_df.dropna(subset=["time", numerator, denominator])
    ratio_df = ratio_df[ratio_df[denominator] != 0]
    ratio_df["analyte_ratio"] = ratio_df[numerator] / ratio_df[denominator]
    return ratio_df[["time", reaction_col, "analyte_ratio"]]


def build_ratio_long_df(
    df: pd.DataFrame,
    reaction_col: str,
    reactant_col: str,
    value_col: str,
    ratio_analytes: list[str],
    numerator: str,
    denominator: str,
) -> pd.DataFrame:
    ratio_df = (
        df[df[reactant_col].astype(str).isin(ratio_analytes)]
        .pivot_table(
            index=["time", reaction_col],
            columns=reactant_col,
            values=value_col,
            aggfunc="mean",
        )
        .reset_index()
    )
    if numerator not in ratio_df.columns or denominator not in ratio_df.columns:
        return pd.DataFrame()
    ratio_df[numerator] = pd.to_numeric(ratio_df[numerator], errors="coerce")
    ratio_df[denominator] = pd.to_numeric(ratio_df[denominator], errors="coerce")
    ratio_df = ratio_df.dropna(subset=["time", numerator, denominator])
    ratio_df = ratio_df[ratio_df[denominator] != 0]
    ratio_df["analyte_ratio"] = ratio_df[numerator] / ratio_df[denominator]
    return ratio_df[["time", reaction_col, "analyte_ratio"]]