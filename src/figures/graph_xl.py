import pandas as pd
import streamlit as st
from streamlit import session_state as _state
import plotly.express as px
import plotly.graph_objects as go
from src.regression.linear_regression import lin_reg

def graph_from_xlsx(df: pd.DataFrame, analytes: list):
    #----Initial Plotting---------------------------------
    if "Time" not in df.columns or "Reactant" not in df.columns:
        st.error("Required columns (Time, Reactant) are missing.")
        return

    df = df[df["Reactant"].isin(analytes)]

    metadata_cols = [
        sample_col,
        "Plate_Number",
        "Well",
        "Injection_Numbers",
        "Sheet_Number",
        "Reactant",
        "RT",
        "Time",
    ]
    all_measurement_cols = df.drop(columns=metadata_cols, errors="ignore").columns.tolist()

    # Preferred measurement columns
    preferred = ["Peak Area", "Peak AP", "Peak RT", "RT"]
    measurement_cols = [c for c in preferred if c in all_measurement_cols]
    measurement_cols += [c for c in all_measurement_cols if c not in measurement_cols and str(c) != "nan"]

    if not measurement_cols:
        st.error("No measurement columns (Peak Area, Peak AP, Peak RT) found.")
        return

    select_meas = st.selectbox("Select measurement to plot", measurement_cols)
    df[select_meas] = pd.to_numeric(df[select_meas], errors="coerce")

    color_options = [c for c in ["Reactant", sample_col, "Plate_Number", "Well"] if c in df.columns]
    color_select = st.radio("Color by:", color_options or ["Reactant"])

    chart_type = st.radio("Chart type", ["Scatter", "Line"], horizontal=True)

    hover_opts = {"Well": True, "Injection_Numbers": True, "RT": True, "Plate_Number": True}


    #----Plotting---------------------------------
    # Incorporate stash sizing here too for consistency
    fig_kwargs = dict(
        width=1200,
        height=500,
        hover_data=hover_opts,
    )

    if chart_type == "Line":
        fig = px.line(
            df,
            x="Time",
            y=select_meas,
            color=color_select,
            markers=True,
            **fig_kwargs,
        )
    else:
        fig = px.scatter(
            df,
            x="Time",
            y=select_meas,
            color=color_select,
            **fig_kwargs,
        )

    for analyte, x_test, y_pred in regression_lines:
        fig.add_trace(
            go.Scatter(
                x=x_test["Time"],
                y=y_pred,
                mode="lines",
                name=f"Linear Regression ({analyte})",
                line=dict(color="black", dash="dash", width=3),
            )
        )

    fig.update_layout(
        title=dict(
            text=f"{select_meas} vs. Time",
            font=dict(size=28),
            x=0.5,
            xanchor="center",
            y=0.95,
            yanchor="top",
        )
    )


    st.plotly_chart(fig, use_container_width=True)
