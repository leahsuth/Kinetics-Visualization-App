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
    if "Time" not in df.columns or "Reactant" not in df.columns:
        st.error("Required columns (Time, Reactant) are missing.")
        return

    sample_col = "Reaction" if "Reaction" in df.columns else "Sample"
    if sample_col in df.columns:
        samples = df[sample_col].unique()
        selected_samples = st.multiselect(
            "Select samples to plot",
            samples,
            default=list(samples) if len(samples) <= 10 else list(samples[:5]),
        )
        if not selected_samples:
            st.warning("Please select at least one sample.")
            return
        df = df[df[sample_col].isin(selected_samples)]

    reactants = df["Reactant"].unique()
    select_reactants = st.multiselect("Select reactants to plot", reactants, default=list(reactants))
    df = df[df["Reactant"].isin(select_reactants)]

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
    st.divider()
    st.subheader("Initial Rate")
    st.caption("Initial rate will be calculated here.")