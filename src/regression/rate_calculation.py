import numpy as np
import pandas as pd
from scipy.optimize import least_squares


def exp_func(C0, Ce, k, t, profile_type):
    """Function to fit the concentration of a reactant or product
    as a function of time, given the initial concentration, saturation
    concentration, rate constant, and time.
    Args:
        C0: initial concentration at t=0
        Ce: saturation concentration at t=inf
        k: rate constant
        t: time range
        profile_type: growth or decay
    Returns:
        C: concentration at time t
    """
    # adjust this function depending on the reaction profile
    if profile_type == "growth":
        C = Ce + (C0 - Ce) * np.exp(-k * t)
        return C

    elif profile_type == "decay":
        C = Ce + (C0 - Ce) * np.exp(-k * t)
        return C

    else:
        raise ValueError("Profile type not recognized")


def residuals(p, Cexp, t, profile_type):
    """Function to calculate the residuals between the experimental
    data and the model.
    Args:
        p: list of parameters to optimize
        Cexp: experimental data
        t: time
        profile_type: growth or decay
    Returns:
        res: residuals
    """

    C0 = p[0]
    Ce = p[1]
    k = p[2]
    Csim = exp_func(C0, Ce, k, t, profile_type)
    res = Csim - Cexp
    return res


def fit_kinetics_and_return_params(
    df: pd.DataFrame,
    analyte: str,
    C0: float,
    Ce: float,
    k: float,
    profile_type: str,
):
    if analyte not in df.columns:
        raise ValueError(f"Analyte {analyte} not present in dataframe")
    if profile_type not in ["decay", "growth"]:
        raise ValueError(f"Profile type: {profile_type} is invalid")

    try:
        experimental = df[analyte].astype(float)
        time = df["time"].astype(float)
    except (TypeError, ValueError):
        return None

    if len(experimental.dropna()) < 3:
        return None

    c_min = float(experimental.min())
    c_max = float(experimental.max())
    c_range = max(c_max - c_min, 1e-6)
    # Bounds to constrain growth vs decay distinctly
    if profile_type == "growth":
        # C0 = initial (low), Ce = equilibrium (high): C0 < Ce
        lb = [c_min - c_range, c_min, 1e-6]
        ub = [c_max, c_max + c_range, 20.0]
    else:
        # Decay: C0 = initial (high), Ce = baseline (low): C0 > Ce
        lb = [c_min, c_min - c_range, 1e-6]
        ub = [c_max + c_range, c_max, 20.0]

    initial_guess = (float(C0), float(Ce), float(k))

    try:
        result = least_squares(
            residuals,
            initial_guess,
            args=(experimental, time, profile_type),
            bounds=(lb, ub),
        )
    except Exception as e:
        return f"Error calculating least_squares: {e}"

    opt = result.x
    return (float(opt[0]), float(opt[1]), float(opt[2]), profile_type)


def kinetics_fit_initial_rate(
    df: pd.DataFrame,
    analyte: str,
    k: float,
    profile_type: str,
    c0_init: float,
    ce_init: float,
):
    """Fit ``df``. Returns ``(rate, C0, Ce, k_fit)`` or ``None`` if the fit fails.
    """
    if len(df) < 3:
        return None

    result = fit_kinetics_and_return_params(
        df,
        analyte,
        float(c0_init),
        float(ce_init),
        float(k),
        profile_type,
    )

    if result is None or isinstance(result, str):
        return None

    C0 = float(result[0])
    Ce = float(result[1])
    k_fit = float(result[2])
    rate = k_fit * (Ce - C0)
    return (rate, C0, Ce, k_fit)


def rate_calculation(
    df: pd.DataFrame,
    analyte: str,
    C0: float,
    Ce: float,
    k: float,
    profile_type: str,
):
    """Function to calculate reaction rate
    Args:
        df (pd.DataFrame): dataframe containing experimental data
        analyte (str): analyte to calculate rate of
        C0 (float): initial concentration of analyte
        Ce (float): saturation concentration at t=inf
        k (float): rate constant
        profile_type (str): "growth" or "decay"
    Returns:
        rate: calculated reaciton rate
    """
    if analyte not in df.columns:
        raise ValueError(f"Analyte {analyte} not present in dataframe")

    if profile_type not in ["growth", "decay"]:
        raise ValueError(f"profile_type: {profile_type} is not a valid setting")

    if k <= 0:
        raise ValueError(f"Invalid value of k: {k}, must be greater than zero")

    df = (df[["time", analyte]].copy().dropna(subset=["time", analyte]).sort_values("time")
    )
    output = kinetics_fit_initial_rate(df, analyte, k, profile_type, float(C0), float(Ce)
    )
    if output is None:
        raise ValueError("Kinetics fit failed (need ≥3 valid time/concentration points)"
        )
    return output[0]
