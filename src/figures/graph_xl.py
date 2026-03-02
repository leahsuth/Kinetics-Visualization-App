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
    #hover_data["_custom_color"] = False

    #----Regression---------------------------------
    if len(df) < 2:
        st.error("Not enough rows for regression.")
        return

    max_index = len(df) - 1
    col1, col2 = st.columns(2)

    with col1:
        start_index = st.number_input("Regression Start Index", min_value=0, max_value=max_index)
    with col2:
        end_index = st.number_input("Regression End Index", min_value=1, max_value=max_index)

    if start_index >= end_index:
        st.error("Start Index must be less than End Index!")
        raise ValueError("start_index greater than end_index")

    regression_lines = []
    models = []
    skipped = []
    df_regression = df.iloc[start_index : end_index + 1].copy()
    for analyte in select_reactants:
        try:
            model, x_test = lin_reg(df_regression, select_meas, 0, len(df_regression) - 1)
            y_pred = model.predict(x_test)
            regression_lines.append((analyte, x_test, y_pred.ravel()))
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
    _state['analytes'] = select_reactants

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

    st.divider()
    st.subheader("Initial Rate")
    st.caption("Initial rate will be calculated here.")