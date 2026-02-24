import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.datasets import load_iris

def lin_reg(df: pd.DataFrame, start_index: int, end_index: int) -> LinearRegression:
    time_present = 'Time' in df.columns
    measurement_present = 'Peak Area' in df.columns

    if not all([time_present, measurement_present]):
        return ValueError('DataFrame does not contain Time or Measurement columns')

    sliced_df = df[start_index : end_index + 1]
    X = sliced_df[['Time']]
    y = sliced_df[['Peak Area']]
    model = LinearRegression()
    model.fit(X,y)

    return model


