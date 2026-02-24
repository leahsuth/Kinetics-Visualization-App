import pandas as pd
from sklearn.linear_model import LinearRegression

def lin_reg(
    df: pd.DataFrame,
    y_col: str,
    start_index: int,
    end_index: int,
) -> tuple[LinearRegression, pd.DataFrame]:
    if "Time" not in df.columns or y_col not in df.columns:
        raise ValueError("DataFrame does not contain required Time or measurement columns.")

    if start_index < 0 or end_index < 0 or start_index > end_index:
        raise ValueError("Invalid regression index range.")

    sliced_df = df.iloc[start_index : end_index + 1].copy()
    sliced_df = sliced_df.dropna(subset=["Time", y_col])
    if len(sliced_df) < 2:
        raise ValueError("Not enough valid points in the selected index range.")

    X = sliced_df[["Time"]]
    y = sliced_df[[y_col]]

    model = LinearRegression()
    model.fit(X, y)

    return model, X

