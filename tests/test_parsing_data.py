import pandas as pd
import pytest
from src.parsing_data import validate_sample_name, melted_rows

#check if columns are missing or if a column has NaN values

def test_missing_sample_name():
    df = pd.DataFrame({"time": [0, 1]})
    with pytest.raises(KeyError):
        validate_sample_name(df)

def test_nan_sample_name():
    df = pd.DataFrame({"sample_name": ["NB-116", None]})
    with pytest.raises(ValueError):
        validate_sample_name(df)

def test_valid_sample_name():
    df = pd.DataFrame({"sample_name": ["NB-116", "NB-121"]})
    validate_sample_name(df)


def test_melt_structure():
    df = pd.DataFrame({"sample_name": ["NB-116", "NB-121"], "reaction_type": ["R", "R"], "time": [0,1], "amine": [1,2],
                        "mono": [3, 4], "di_same_ring": [5,6]})
    col_name = ["sample_name", "reaction_type", "time"]
    analytes = [col for col in df.columns if col not in col_name]
    melted_df = pd.melt(df, col_name, analytes, "molecule", "concentration")
    assert len(melted_df) == len(df) * len(analytes)
    assert set(melted_df["molecule"]) == set(analytes)

#also check to see if negative values are clipped
