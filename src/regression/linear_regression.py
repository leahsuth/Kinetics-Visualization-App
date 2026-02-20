import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.datasets import load_iris

def lin_reg(col: pd.Series, start_index: int, end_index: int) -> LinearRegression:
    sliced_col = col[start_index : end_index]
    pass

