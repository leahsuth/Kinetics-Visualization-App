from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
from plotly.graph_objects import Figure

def _reaction_title_suffix(reactions: pd.Series) -> str | None:
    s = reactions.dropna()
    if s.empty or s.nunique() <= 1:
        return None
    num = pd.to_numeric(s, errors="coerce")
    if num.notna().all():
        vals = sorted(num.unique().tolist())
        if all(float(v) == int(float(v)) for v in vals):
            return "Reactions " + ", ".join(str(int(v)) for v in vals)
        return "Reactions " + ", ".join(str(v) for v in vals)
    return "Reactions " + ", ".join(sorted(s.astype(str).unique()))


def build_preprocessed_figure(
    df: pd.DataFrame,
    color_select: str,
    chart_type: str,
    time_unit: str = "hours",
    title_suffix: str | None = None,
    measurement_type: str = "Concentration",
    colorblind_shapes: bool = False,
) -> tuple[Figure | None, str | None]:
    """
    Build the Plotly figure for preprocessed kinetics (no Streamlit).
    Returns (figure, None) on success, or (None, error_message).
    """
    df = df.copy()
    if "time" not in df.columns and "Time" in df.columns:
        df = df.rename(columns={"Time": "time"})
    if "time" not in df.columns:
        return None, 'Preprocessed data must include a "time" or "Time" column.'
    if "Reaction" not in df.columns:
        return None, 'Preprocessed data must include a "Reaction" column.'

    if title_suffix is None:
        title_suffix = _reaction_title_suffix(df["Reaction"])

    skip_numeric = {"Reaction", "Sample Name"}
    skip_melt = {"time", "Reaction", "Sample Name"}
    for col in df.columns:
        if col in skip_numeric:
            continue
        df[col] = pd.to_numeric(df[col], errors="coerce")

    analytes = [c for c in df.columns if c not in skip_melt]
    id_vars = ["time", "Reaction"]

    melted_df = df.melt(
        id_vars=id_vars,
        value_vars=analytes,
        var_name="Analyte",
        value_name="Concentration",
    ).dropna(subset=["Concentration"])

    melted_df["Reaction"] = melted_df["Reaction"].astype(str)

    hover_opts = {"time": True, "Concentration": True, "Analyte": True}

    melted_df["_series_group"] = (
        melted_df["Reaction"].astype(str)
        + " | "
        + melted_df["Analyte"].astype(str)
    )

    fig_kwargs = dict(
        width=1200,
        height=500,
        hover_data=hover_opts,
    )

    qualitative_colors = px.colors.qualitative.Plotly

    symbol_sequence = [
        "circle",
        "square",
        "diamond",
        "cross",
        "x",
        "triangle-up",
        "triangle-down",
        "triangle-left",
        "triangle-right",
        "pentagon",
        "hexagon",
        "star",
        "hourglass",
        "bowtie",
    ]

    if chart_type == "Line":
        if colorblind_shapes:
            fig = px.line(
                melted_df,
                x="time",
                y="Concentration",
                color=color_select,
                line_group="_series_group",
                color_discrete_sequence=qualitative_colors,
                symbol="Analyte",
                symbol_sequence=symbol_sequence,
                markers=True,
                **fig_kwargs,
            )
        else:
            fig = px.line(
                melted_df,
                x="time",
                y="Concentration",
                color=color_select,
                line_group="_series_group",
                color_discrete_sequence=qualitative_colors,
                markers=True,
                **fig_kwargs,
            )
        fig.update_traces(marker=dict(size=10))
    else:
        if colorblind_shapes:
            fig = px.scatter(
                melted_df,
                x="time",
                y="Concentration",
                color=color_select,
                color_discrete_sequence=qualitative_colors,
                symbol="Analyte",
                symbol_sequence=symbol_sequence,
                **fig_kwargs,
            )
        else:
            fig = px.scatter(
                melted_df,
                x="time",
                y="Concentration",
                color=color_select,
                color_discrete_sequence=qualitative_colors,
                **fig_kwargs,
            )
        fig.update_traces(marker=dict(size=10))

    title_text = f"{measurement_type} vs. Time"
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
    fig.update_yaxes(title_text=measurement_type)

    return fig, None


def graph_preprocessed_data(
    df: pd.DataFrame,
    color_select: str,
    chart_type: str,
    time_unit: str = "hours",
    title_suffix: str | None = None,
    colorblind_shapes: bool = False,
):
    meas = st.session_state.get("measurement_type", "Concentration")
    fig, err = build_preprocessed_figure(
        df,
        color_select,
        chart_type,
        time_unit,
        title_suffix=title_suffix,
        measurement_type=meas,
        colorblind_shapes=colorblind_shapes,
    )
    if err:
        st.error(err)
        return
    st.plotly_chart(fig, width="stretch")
