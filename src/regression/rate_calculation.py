import numpy as np
import pandas as pd
from scipy.optimize import least_squares

def exp_func(C0,Ce,k,t, profile_type):
    '''Function to fit the concentration of a reactant or product
    as a function of time, given the initial concentration, saturation
    concentration, rate constant, and time.
    Args:
        C0: initial concentration at t=0
        Ce: saturation concentration at t=inf
        k: rate constant
        t: time
        profile_type: growth or decay
    Returns:
        C: concentration at time t
    '''
    # adjust this function depending on the reaction profile
    if profile_type == 'growth':
        C = Ce + (C0-Ce)*np.exp(-k*t)
        return C
    
    elif profile_type == 'decay':
        C = C0*np.exp(-k*t)+Ce
        return C
    
    else:
        raise ValueError('Profile type not recognized')

def residuals(p,Cexp,t, profile_type):
    '''Function to calculate the residuals between the experimental
    data and the model.
    Args:
        p: list of parameters to optimize
        Cexp: experimental data
        t: time
        profile_type: growth or decay
    Returns:
        res: residuals
    '''
    
    C0 = p[0]
    Ce = p[1]
    k = p[2]
    Csim = exp_func(C0,Ce,k,t, profile_type)
    res = (Csim-Cexp)
    return res

def rate_calculation(
    df: pd.DataFrame,
    analyte: str,
    C0: float,
    Ce: float,
    k: float,
    profile_type: str = "decay",
):
    '''Function to calculate reaction rate
    Args:
        df (pd.DataFrame): dataframe containing experimental data
        analyte (str): analyte to calculate rate of
        C0 (float): initial concentration of analyte
        Ce (float): saturation concentration at t=inf
        k (float): rate constant
        profile_type (str): "growth" or "decay"
    Returns:
        rate: calculated reaciton rate
    '''
    if analyte not in df.columns:
        raise ValueError(f"Analyte {analyte} not present in dataframe")

    experimental = df[analyte]
    time = df["Time"]
    initial_guess = (C0, Ce, k)

    result = least_squares(
        residuals, initial_guess, args=(experimental, time, profile_type)
    )

    # if not result.success:
    #     status = result.status
    #     raise ValueError(f'Least Squares failed with a status of {status}')
        
    opt_params = result.x # optimized parameters
    par = {
        "C0": opt_params[0],
        "Ce": opt_params[1],
        "k": opt_params[2],
    }

    # time at which rate is calculated, for initial rate, t_rate = 0
    t_rate = 0

    rate = par['C0'] * (par['k']) * np.exp(-t_rate * (par['k']))

    return rate
