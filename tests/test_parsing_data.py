import pandas as pd
import pytest
from src.parsing_data import process_data, standardize_data_realdata, add_time


def test_process_data_csv_renames_first_column(tmp_path):
    csv_path = tmp_path / "input.csv"
    df = pd.DataFrame({"First": ["A", "B"], "Value": [1, 2]})
    df.to_csv(csv_path, index=False)

    result = process_data(str(csv_path))

    assert result.columns[0] == "Sample Name"
    assert result["Sample Name"].tolist() == ["A", "B"]


def test_process_data_excel_without_peak_rt(tmp_path):
    xlsx_path = tmp_path / "input.xlsx"
    df = pd.DataFrame(
        {
            "Col1": ["RXN1", "RXN2"],
            "Col2": ["P1-A1", "A2"],
            "Col3": [1, 2],
            "Extra": [10, 20],
        }
    )
    df.to_excel(xlsx_path, index=False, sheet_name="Sheet1")

    result = process_data(str(xlsx_path))

    assert "Reaction" in result.columns
    assert "Well" in result.columns
    assert "Injection_Numbers" in result.columns
    assert "Plate_Number" in result.columns
    assert "Sheet_Number" in result.columns
    assert result.loc[0, "Plate_Number"] == "P1"
    assert result.loc[0, "Well"] == "A1"
    assert result.loc[1, "Plate_Number"] == "AAA"
    assert result.loc[1, "Well"] == "A2"


def test_process_data_excel_with_peak_rt(tmp_path):
    xlsx_path = tmp_path / "input_peak_rt.xlsx"
    columns = pd.MultiIndex.from_tuples(
        [
            ("Reaction", "Peak RT"),
            ("Well", "Peak RT"),
            ("Injection", "Peak RT"),
            ("RT_1.0", "Peak Area"),
        ]
    )
    df = pd.DataFrame(
        [
            ["RXN1", "P2-B1", 1, 123.4],
            ["RXN2", "B2", 2, 456.7],
        ],
        columns=columns,
    )
    df.to_excel(xlsx_path, index=False, sheet_name="Sheet1")

    result = process_data(str(xlsx_path))

    assert "Reaction" in result.columns
    assert "Well" in result.columns
    assert "Injection_Numbers" in result.columns
    assert "RT_1.0__Peak Area" in result.columns
    assert "Sheet_Number" in result.columns
    assert result.loc[0, "Plate_Number"] == "P2"
    assert result.loc[0, "Well"] == "B1"


def test_standardize_data_realdata_pivots_measurements():
    df = pd.DataFrame(
        {
            "Reaction": ["RXN1"],
            "Plate_Number": ["AAA"],
            "Well": ["A1"],
            "Injection_Numbers": [1],
            "RT_1.0__Peak Area": [10.5],
            "RT_1.0__Peak Height": [2.5],
        }
    )

    result = standardize_data_realdata(df, save_as_csv=False)

    assert "Reactant" in result.columns
    assert "RT" in result.columns
    assert "Peak Area" in result.columns
    assert "Peak Height" in result.columns
    assert result.loc[0, "Reactant"] == "1.0"
    assert result.loc[0, "RT"] == "1.0"
    assert result.loc[0, "Peak Area"] == 10.5
    assert result.loc[0, "Peak Height"] == 2.5


def test_add_time_row_and_col(tmp_path, monkeypatch):
    df = pd.DataFrame({"Well": ["A1", "B2"]})

    monkeypatch.chdir(tmp_path)
    add_time(df.copy(), row=True, col=False)
    row_result = pd.read_csv(tmp_path / "final_data.csv")
    assert row_result["Time"].tolist() == [1, 2]

    add_time(df.copy(), row=False, col=True)
    col_result = pd.read_csv(tmp_path / "final_data.csv")
    assert col_result["Time"].tolist() == [1, 2]


def test_add_time_raises_when_no_axis():
    df = pd.DataFrame({"Well": ["A1"]})
    with pytest.raises(ValueError):
        add_time(df, row=False, col=False)
