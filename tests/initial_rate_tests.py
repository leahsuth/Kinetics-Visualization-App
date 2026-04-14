import pandas as pd
import pytest
from pathlib import Path

from src.regression.rate_calculation import kinetics_fit_initial_rate, rate_calculation
from src.parsing.parsing_data import process_manual

DATA = Path(__file__).resolve().parents[1] / "data"
CONDITIONS = DATA / "NB-0123-0005_Cat_Loading_Conditions.xlsx"
HPLC_DATA = DATA / "NB-0123-0005_Cat_Loading_Data.xlsx"
RATES_FILE = DATA / "NB-0123-0005_Cat_Loading_Initial_Rates.xlsx"

_rates_df = pd.read_excel(RATES_FILE, engine="openpyxl")


def _profile_picker(C0: float, Ce: float) -> str:
    """Same rule as src.page_styling.rate_information.profile_picker (no streamlit import)."""
    return "decay" if C0 > Ce else "growth"


@pytest.fixture(scope="module")
def merged_df():
    return process_manual(str(CONDITIONS), str(HPLC_DATA), save_as_csv=False)


@pytest.mark.parametrize("rxn_num", _rates_df["Reaction_Number"].tolist())
def test_rate_calculation_matches_kinetics_fit(rxn_num, merged_df):
    """rate_calculation must use the same bounds as kinetics_fit_initial_rate."""
    rxn_df = merged_df[merged_df["reaction"] == rxn_num].copy()
    product_df = rxn_df[rxn_df["reactant"] == "Product"].reset_index(drop=True)

    C0 = float(product_df["peak_ap"].iloc[0])
    Ce = float(product_df["peak_ap"].iloc[-1])
    profile_type = _profile_picker(C0, Ce)

    single_df = (
        product_df[["time", "peak_ap"]]
        .dropna(subset=["time", "peak_ap"])
        .sort_values("time")
    )
    rate = rate_calculation(
        product_df, "peak_ap", C0, Ce, k=0.5, profile_type=profile_type
    )
    out = kinetics_fit_initial_rate(
        single_df, "peak_ap", 0.5, profile_type, C0, Ce
    )
    assert out is not None, f"Reaction {rxn_num}: fit failed"
    expected = out[0]
    tol = 0.05  # 5% relative tolerance for good fits
    assert abs(rate - expected) / (abs(expected) + 1e-9) < tol, (
        f"Reaction {rxn_num}: rate_calculation {rate:.6f} vs kinetics_fit_initial_rate {expected:.6f}"
    )
