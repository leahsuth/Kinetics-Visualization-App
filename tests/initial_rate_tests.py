import pandas as pd
import pytest
from pathlib import Path

from src.regression.rate_calculation import rate_calculation
from src.parsing.parsing_data import process_manual

DATA = Path(__file__).resolve().parents[1] / "data"
CONDITIONS = DATA / "NB-0123-0005_Cat_Loading_Conditions.xlsx"
HPLC_DATA  = DATA / "NB-0123-0005_Cat_Loading_Data.xlsx"
RATES_FILE = DATA / "NB-0123-0005_Cat_Loading_Initial_Rates.xlsx"

@pytest.fixture(scope="module")
def expected_rates():
    df = pd.read_excel(RATES_FILE, engine="openpyxl")
    return dict(zip(df["Reaction_Number"], df["Initiate_Rate"]))

# Load the full merged pipeline output once
@pytest.fixture(scope="module")
def merged_df():
    return process_manual(str(CONDITIONS), str(HPLC_DATA))

# Build parametrize list from the rates file at collection time
_rates_df = pd.read_excel(RATES_FILE, engine="openpyxl")


@pytest.mark.parametrize("rxn_num", _rates_df["Reaction_Number"].tolist())
def test_initial_rate_per_reaction(rxn_num, merged_df, expected_rates):
    expected = expected_rates[rxn_num]

    rxn_df = merged_df[merged_df["reaction"] == rxn_num].copy()
    product_df = rxn_df[rxn_df["reactant"] == "Product"].reset_index(drop=True)

    # Need to change values to match the inputs in the expected rates
    C0 = float(product_df["peak_area"].iloc[0])
    Ce = float(product_df["peak_area"].iloc[-1])

    rate = rate_calculation(
        product_df, "peak_area",
        C0=C0, Ce=Ce, k=0.5,
        profile_type="growth",
    )

    tol = 0.01  # 1.0% tolerance for good fits
    assert abs(rate - expected) / (abs(expected) + 1e-9) < tol, (
        f"Reaction {rxn_num}: got {rate:.4f}, expected {expected:.4f}"
    )
