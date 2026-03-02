import pandas as pd
import streamlit as st
import plotly.express as px


# ----------------------------
# CSV plotting
# ----------------------------
def graph_from_csv(df: pd.DataFrame, analytes: list | None = None):
    # Require Time
    if "Time" not in df.columns:
        st.error('CSV must include a "Time" column.')
        return

    # Candidate analyte columns (everything except common metadata)
    analyte_cols = df.drop(columns=["Sample Name", "Time"], errors="ignore").columns.tolist()

    # Default selection: use analytes arg if provided, otherwise none (empty list)
    default = [a for a in (analytes or []) if a in analyte_cols]

    selected = st.multiselect("Select analytes to plot", analyte_cols, default=default)
    if not selected:
        st.info("Please select at least one analyte to plot.")
        return

    chart_type = st.radio("Chart type", ["Scatter", "Line"], horizontal=True)

    # Make a copy and coerce selected analytes to numeric
    df2 = df.copy()
    for c in selected:
        df2[c] = pd.to_numeric(df2[c], errors="coerce")

    melted_df = df2.melt(
        id_vars=["Time"],
        value_vars=selected,
        var_name="Analyte",
        value_name="Concentration",
    ).dropna(subset=["Concentration"])

    hover_opts = {"Time": True, "Concentration": True, "Analyte": True}

    # Incorporate stash sizing (consistent for both line/scatter)
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

    st.plotly_chart(fig, use_container_width=True)
    st.divider()
    st.subheader("Initial Rate")
    st.caption("Initial rate will be calculated here.")


# ----------------------------
# XLSX plotting
# ----------------------------
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
        return

    # Filter using the same string form
    df = df[df["reaction"].astype(str).isin(selected_reactions)]

    reactants = df["reactant"].unique()
    select_reactants = st.multiselect("Select reactants to plot", reactants, default=list(reactants))
    df = df[df["reactant"].isin(select_reactants)]

    preferred = ["peak_area", "peak_ap"]
    measurement_cols = [c for c in preferred if c in df.columns]

    if not measurement_cols:
        raise ValueError("No peak_area or peak_ap columns found in dataframe.")

    select_meas = st.selectbox("Select measurement to plot", measurement_cols)
    df[select_meas] = pd.to_numeric(df[select_meas], errors="coerce")

    color_options = [c for c in ["reactant", "reaction"] if c in df.columns]
    color_select = st.radio("Color by:", color_options or ["reactant"])

    # Sort the dataframe by reaction, reactant, and time for line plot
    df = df.sort_values(by=["reaction", "reactant", "time"])
    chart_type = st.radio("Chart type", ["Scatter", "Line"], horizontal=True)

    # hover_opts = {"Well": True, "Injection_Numbers": True, "RT": True, "Plate_Number": True}

    # Hover: all columns, but hide Plotly’s internal _custom_color (dict form excludes it from tooltip)
    hover_data = {c: True for c in df.columns}
    hover_data["_custom_color"] = False

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
    st.divider()
    st.subheader("Initial Rate")
    st.caption("Initial rate will be calculated here.")
