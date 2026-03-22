from pathlib import Path

import pandas as pd
import pytest

from src.parsing.parsing_data import process_data

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CSV_PATH = DATA_DIR / "Example_Data_SpiroXantPhos.csv"
XLSX_TWO_SHEETS_PATH = DATA_DIR / "Example_ChemStation_Data_GPT_TWOSHEETSONEEXPERIMENT.xlsx"
XLSX_ONE_SHEET_PATH = DATA_DIR / "Example_ChemStation_Data_NB-0123-0002_ONESHEET.xlsx"


def test_process_data_csv_renames_first_column():
    result = process_data(str(CSV_PATH))

    assert result.columns[0] == "Sample Name"
    assert result["Sample Name"].notna().all()
    assert len(result) > 0


def test_process_data_excel_two_sheets():
    result = process_data(str(XLSX_TWO_SHEETS_PATH))

    assert "Reaction" in result.columns
    assert "Well" in result.columns
    assert "Injection_Numbers" in result.columns
    assert "Plate_Number" in result.columns
    assert "Sheet_Number" in result.columns
    assert result["Plate_Number"].notna().all()
    assert result["Well"].str.contains("-").sum() == 0
    assert set(result["Sheet_Number"].unique()) == {0, 1}
    assert len(result) > 0


def test_process_data_excel_one_sheet():
    result = process_data(str(XLSX_ONE_SHEET_PATH))

    assert "Reaction" in result.columns
    assert "Well" in result.columns
    assert "Injection_Numbers" in result.columns
    assert "Plate_Number" in result.columns
    assert "Sheet_Number" in result.columns
    assert result["Plate_Number"].notna().all()
    assert result["Well"].str.contains("-").sum() == 0
    assert set(result["Sheet_Number"].unique()) == {0}
    assert len(result) > 0


def test_standardize_data_realdata_pivots_measurements():
    df = process_data(str(XLSX_ONE_SHEET_PATH))

    result = standardize_data_realdata(df, save_as_csv=False)

    assert "Reactant" in result.columns
    assert "RT" in result.columns
    assert "Reaction" in result.columns
    assert "Plate_Number" in result.columns
    assert "Well" in result.columns
    assert "Injection_Numbers" in result.columns

    measurement_cols = {
        col for col in result.columns
        if col
        not in {"Reaction", "Plate_Number", "Well", "Injection_Numbers", "Sheet_Number", "Reactant", "RT"}
    }
    assert len(measurement_cols) > 0
    assert result["Reactant"].notna().all()
    assert result["RT"].notna().all()
    assert len(result) > 0


def test_add_time_row_and_col(tmp_path, monkeypatch):
    df = process_data(str(XLSX_ONE_SHEET_PATH))
    wells = df["Well"].astype(str).str.extract(r"^([A-H]\d+)$")[0].dropna()
    assert len(wells) >= 2
    sample_wells = wells.iloc[:2].tolist()
    small_df = pd.DataFrame({"Well": sample_wells})

    mapping = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8}
    expected_row = [mapping[w[0]] for w in sample_wells]
    expected_col = [int("".join(filter(str.isdigit, w))) for w in sample_wells]

    monkeypatch.chdir(tmp_path)
    add_time(small_df.copy(), row=True, col=False)
    row_result = pd.read_csv(tmp_path / "final_data.csv")
    assert row_result["Time"].tolist() == expected_row

    add_time(small_df.copy(), row=False, col=True)
    col_result = pd.read_csv(tmp_path / "final_data.csv")
    assert col_result["Time"].tolist() == expected_col


def test_add_time_raises_when_no_axis():
    df = pd.DataFrame({"Well": ["A1"]})
    with pytest.raises(ValueError):
        add_time(df, row=False, col=False)
