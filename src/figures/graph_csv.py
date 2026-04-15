import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

def graph_from_csv(df: pd.DataFrame, analytes: list | None = None):
    #----Initial Plotting---------------------------------
    # Require Time
    if "Time" not in df.columns:
        st.error('CSV must include a "Time" column.')
        return

    chart_type = st.radio("Chart type", ["Scatter", "Line"], horizontal=True)

    # Make a copy and coerce Time + selected analytes to numeric
    df2 = df.copy()
    df2["Time"] = pd.to_numeric(df2["Time"], errors="coerce")
    for c in analytes:
        df2[c] = pd.to_numeric(df2[c], errors="coerce")

    melted_df = df2.melt(
        id_vars=["Time"],
        value_vars=analytes,
        var_name="Analyte",
        value_name="Concentration",
    ).dropna(subset=["Concentration"])

    hover_opts = {"Time": True, "Concentration": True, "Analyte": True}


    #----Plotting---------------------------------
    fig_kwargs = dict(
        width=1200,
        height=500,
        hover_data=hover_opts,
    )

    if chart_type == "Line":
        fig = px.line(
            melted_df,
            x="Time",
            y="Concentration",
            color="Analyte",
            markers=True,
            **fig_kwargs,
        )
    else:
        fig = px.scatter(
            melted_df,
            x="Time",
            y="Concentration",
            color="Analyte",
            **fig_kwargs,
        )

    # Single source of truth for title styling
    fig.update_layout(
        title=dict(
            text="Concentration vs. Time",
            font=dict(size=28),
            x=0.5,
            xanchor="center",
            y=0.95,
            yanchor="top",
        )
    )

    st.plotly_chart(fig, width="stretch")
