import pandas as pd
import streamlit as st
from streamlit import session_state as _state
import plotly.express as px
import plotly.graph_objects as go
from src.regression.linear_regression import lin_reg


def graph_from_xlsx(df: pd.DataFrame, selected_reactions: list, select_reactants: list, select_meas: str = "peak_area"):
    # Clean reaction values for the UI; sort numerically (1, 2, ..., 10, ...) for selector

    #----Initial Plotting---------------------------------

    color_options = [c for c in ["reactant", "reaction"] if c in df.columns]
    color_select = st.radio("Color by:", color_options or ["reactant"])

    # Sort the dataframe by reaction, reactant, and time for line plot
    df = df.sort_values(by=["reaction", "reactant", "time"])
    chart_type = st.radio("Chart type", ["Scatter", "Line"], horizontal=True)
    # Hover: all columns, but hide Plotly’s internal _custom_color (dict form excludes it from tooltip)
    hover_data = {c: True for c in df.columns}
    #hover_data["_custom_color"] = False

    #----Plotting---------------------------------
    # Incorporate stash sizing here too for consistency
    fig_kwargs = dict(
        width=1200,
        height=500
    )

    if chart_type == "Line":
        fig = px.line(
            df,
            x="time",
            y=select_meas,
            color=color_select,
            hover_data=hover_data,
            markers=True,
            **fig_kwargs,
        )
    else:
        fig = px.scatter(
            df,
            x="time",
            y=select_meas,
            color=color_select,
            hover_data=hover_data,
            **fig_kwargs,
        )

    fig.update_layout(
        title=dict(
            text=f"{select_meas} vs. time",
            font=dict(size=28),
            x=0.5,
            xanchor="center",
            y=0.95,
            yanchor="top",
        )
    )


    st.plotly_chart(fig, use_container_width=True)

    first_line = st.session_state["first_line"]
    st.caption(first_line)
    return fig 
