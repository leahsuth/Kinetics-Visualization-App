import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.datasets import load_iris

def lin_reg(df: pd.DataFrame, start_index: int, end_index: int) -> LinearRegression:
    time_present = 'Time' in df.columns
    measurement_present = 'Measurement' in df.columns

    if all([time_present, measurement_present]) not in df.columns:
        return ValueError('DataFrame does not contain Time or Measurement columns')

    sliced_df = df[start_index : end_index]
    X = sliced_df['Time']
    y = sliced_df['Measurement']
    pass


