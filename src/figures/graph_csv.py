import pandas as pd
import streamlit as st
from streamlit import session_state as _state
import plotly.express as px
import plotly.graph_objects as go
from src.parsing.parsing_data import add_time  # keep if used elsewhere; remove if unused
from src.regression.linear_regression import lin_reg

def graph_from_csv(df: pd.DataFrame, analytes: list | None = None):
    #----Initial Plotting---------------------------------
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

    # Make a copy and coerce Time + selected analytes to numeric
    df2 = df.copy()
    df2["Time"] = pd.to_numeric(df2["Time"], errors="coerce")
    for c in selected:
        df2[c] = pd.to_numeric(df2[c], errors="coerce")

    melted_df = df2.melt(
        id_vars=["Time"],
        value_vars=selected,
        var_name="Analyte",
        value_name="Concentration",
    ).dropna(subset=["Concentration"])

    hover_opts = {"Time": True, "Concentration": True, "Analyte": True}

    #----Regression---------------------------------
    if len(df2) < 2:
        st.error("Not enough rows for regression.")
        return

    # Inpute for Regression Range
    max_index = len(df2) - 1
    col1, col2 = st.columns(2)

    with col1:
        start_index = st.number_input("Regression Start Index", min_value=0, max_value=max_index)
    with col2:
        end_index = st.number_input("Regression End Index", min_value=1, max_value=max_index)

    if start_index >= end_index:
        st.error("Start Index must be less than End Index!")
        return

    # create models for each analyte in the provided range
    regression_lines = []
    models = []
    skipped = []
    df_regression = df2.iloc[start_index : end_index + 1].copy()
    for analyte in selected:
        try:
            model, x_test = lin_reg(df_regression, analyte, 0, len(df_regression) - 1)
            y_pred = model.predict(x_test)
            regression_lines.append((analyte, x_test["Time"].to_numpy(), y_pred.ravel()))
            models.append(model)
        except ValueError:
            skipped.append(analyte)
        except Exception as err:
            st.error(f"Regression Failed: {err}")
            return

    if skipped:
        st.warning(f"Skipped regression for: {', '.join(skipped)} (not enough points in range).")

    # Save Plotted Ranges to state
    _state['regression_lines'] = regression_lines
    _state['regression_models'] = models
    # Incorporate stash sizing (consistent for both line/scatter)

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

    for analyte, x_vals, y_vals in regression_lines:
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=y_vals,
                mode="lines",
                name=f"Linear Regression ({analyte})",
                line=dict(color="black", dash="dash", width=3),
            )
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
