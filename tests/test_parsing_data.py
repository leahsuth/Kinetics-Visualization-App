from pathlib import Path

import pandas as pd
import pytest

from src.parsing.parsing_data import process_data, process_manual

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CSV_PATH = DATA_DIR / "Example_Data_SpiroXantPhos.csv"
XLSX_TWO_SHEETS_PATH = DATA_DIR / "Example_ChemStation_Data_GPT_TWOSHEETSONEEXPERIMENT.xlsx"
XLSX_ONE_SHEET_PATH = DATA_DIR / "Example_ChemStation_Data_NB-0123-0002_ONESHEET.xlsx"
CONFIG_PATH = DATA_DIR / "NB-0123-0005_Cat_Loading_Conditions.xlsx"
DATA_PATH = DATA_DIR / "NB-0123-0005_Cat_Loading_Data.xlsx"

@pytest.fixture
def result():
    return process_manual(str(CONFIG_PATH), str(DATA_PATH), False)

@pytest.fixture
def config_df():
    return pd.read_excel(str(CONFIG_PATH))

def test_process_data_csv_renames_first_column(result):

    assert result.columns[0] == "sample_name"
    assert result["sample_name"].notna().all()
    assert len(result) > 0

def test_processed_date_shape(result):
    target_cols = [
        'sample_name',
        'reaction',
        'sample_number',
        'timepoint_number',
        'time',
        'ligand',
        'catalyst_loading',
        'reactant',
        'peak_ap',
        'peak_area'
    ]

    for col in target_cols:
        assert col in result.columns

    assert len(target_cols) == len(result.columns)

def test_reaction_number(result, config_df):
    assert result['reaction'].nunique() == config_df['Reaction_Number'].nunique()

def test_time_points(result, config_df):
    assert result['time'].nunique() == config_df['Timepoints_h'].nunique()
