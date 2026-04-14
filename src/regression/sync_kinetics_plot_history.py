import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .rate_calculation import exp_func, kinetics_fit_initial_rate


def sync_kinetics_plot_history(history, k_constant, time_unit, y_measure_label):
    """Recompute fit, rate box, and curve from current k to match the Rate Summary table."""
    for item in history:
        single_df = item["single_df"]
        analyte = item["analyte"]
        profile_type = item["profile_type"]
        rxn = item["reaction"]
        C0_init = float(single_df[analyte].iloc[0])
        Ce_init = float(single_df[analyte].iloc[-1])
        out = kinetics_fit_initial_rate(single_df, analyte, k_constant, profile_type, C0_init, Ce_init)
        if out is None:
            continue

        rate_val, C0, Ce, k_fit = out
        t_fine = np.linspace(float(single_df["time"].min()),float(single_df["time"].max()),100,)
        y_fit = exp_func(C0, Ce, k_fit, t_fine, profile_type)
        # Update rate table with new rate
        item["rate_table"] = pd.DataFrame([{"Reaction": rxn, "Analyte": analyte, "Profile": profile_type, "Rate": rate_val,
            "C0": C0,"Ce": Ce,"k": k_fit,
        }])
        item["t_fine"] = t_fine.tolist()
        item["y_fit"] = y_fit.tolist()
        # Create new figure with updated fit and rate
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=single_df["time"], y=single_df[analyte], mode="markers", name="data"))
        fig.add_trace(go.Scatter(x=t_fine, y=y_fit, mode="lines", name="fitted curve", line=dict(color="#E53935", width=2)))
        fig.update_layout(title=f"{analyte} - Reaction {rxn}", xaxis_title=f"Time ({time_unit})", yaxis_title=y_measure_label,
        width=400, height=250)
        item["fig"] = fig
