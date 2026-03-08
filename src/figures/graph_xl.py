import pandas as pd
import streamlit as st
from streamlit import session_state as _state
import plotly.express as px
import plotly.graph_objects as go
from src.regression.linear_regression import lin_reg


def graph_from_xlsx(df: pd.DataFrame):
    # Clean reaction values for the UI; sort numerically (1, 2, ..., 10, ...) for selector
    raw = df["reaction"].dropna().unique().tolist()
    try:
        reactions = [str(r) for r in sorted(raw, key=lambda x: float(x))]
    except (TypeError, ValueError):
        reactions = sorted(str(r) for r in raw)

    selected_reactions = st.multiselect(
        "Select reaction to plot",
        reactions,
        default=reactions if len(reactions) <= 10 else reactions[:5],
    )
    if not selected_reactions:
        st.warning("Please select at least one reaction.")

    #----Initial Plotting---------------------------------
    # Filter using the same string form
    df = df[df["reaction"].astype(str).isin(selected_reactions)]

    reactants = df["reactant"].unique()
    select_reactants = st.multiselect("Select reactants to plot", reactants, default=list(reactants))
    df = df[df["reactant"].isin(select_reactants)]

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

    select_meas = st.selectbox("Select measurement to plot", measurement_cols)
    df[select_meas] = pd.to_numeric(df[select_meas], errors="coerce")
    df = df.dropna(subset=["time", select_meas])

    color_options = [c for c in ["reactant", "reaction"] if c in df.columns]
    color_select = st.radio("Color by:", color_options or ["reactant"])

    # Sort the dataframe by reaction, reactant, and time for line plot
    df = df.sort_values(by=["reaction", "reactant", "time"])
    chart_type = st.radio("Chart type", ["Scatter", "Line"], horizontal=True)

    # hover_opts = {"Well": True, "Injection_Numbers": True, "RT": True, "Plate_Number": True}

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
