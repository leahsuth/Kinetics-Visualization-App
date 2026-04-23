import io
import pandas as pd
from openpyxl.styles import Border


def excel_template_bytes_HPLC() -> bytes:
    df = pd.DataFrame(
        [
            {
                "Timepoint": "0",
                " ": "",
                "  ": "",
                "Reaction": "1",
                "Reaction_Well": "A1",
                "Condition1": "LigA",
                "Condition2": "Cat1",
            },
            {
                "Timepoint": "5",
                " ": "",
                "  ": "",
                "Reaction": "2",
                "Reaction_Well": "A2",
                "Condition1": "",
                "Condition2": "Cat2",
            },
            {
                "Timepoint": "10",
                " ": "",
                "  ": "",
                "Reaction": "",
                "Reaction_Well": "",
                "Condition1": "",
                "Condition2": "",
            },
        ]
    )
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Experiment")
        worksheet = writer.sheets["Experiment"]
        for spacer_col in (" ", "  "):
            spacer_col_idx = df.columns.get_loc(spacer_col) + 1
            header_cell = worksheet.cell(row=1, column=spacer_col_idx)
            header_cell.border = Border()
    return buf.getvalue()


def excel_template_bytes_Processed() -> bytes:
    df = pd.DataFrame(
        [
            {"Reaction": "1", "Num_Timepoints": "10", "Reaction_Well": "A1", "Condition1": "LigA", "Condition2": "Cat1"},
            {"Reaction": "2", "Num_Timepoints": "18", "Reaction_Well": "", "Condition1": "", "Condition2": ""},
            {"Reaction": "3", "Num_Timepoints": "24", "Reaction_Well": "", "Condition1": "", "Condition2": ""},
        ]
    )
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Experiment")
    return buf.getvalue()
