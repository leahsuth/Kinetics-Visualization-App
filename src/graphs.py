import pandas as pd
import streamlit as st
import plotly.express as px

def graph_from_csv(df: pd.DataFrame, analytes: list | None = None):
    # Require Time
    if "Time" not in df.columns:
        st.error('CSV must include a "Time" column.')
        return

    # Candidate analyte columns (everything except common metadata)
    analyte_cols = df.drop(columns=["Sample Name", "Time"], errors="ignore").columns.tolist()

    # Default selection: use analytes arg if provided, otherwise none
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

    if chart_type == "Line":
        fig = px.line(
            melted_df,
            x="Time",
            y="Concentration",
            color="Analyte",
            markers=True,
            hover_data=hover_opts,
            title="Concentration vs. Time",
            width=1200,
            height=500,
        )
    else:
        fig = px.scatter(
            melted_df,
            x="Time",
            y="Concentration",
            color="Analyte",
            hover_data=hover_opts,
            title="Concentration vs. Time",
            width=1200,
            height=500,
        )

    fig.update_layout(
    title=dict(
        text="Concentration vs. Time",
        font=dict(size=28),
        x=0.5,          # center title
        xanchor="center",
        y=0.95,
        yanchor="top")
  )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Initial Rate")
    st.caption("Initial rate will be calculated here.")
