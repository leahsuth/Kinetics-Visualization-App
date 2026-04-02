import io
from pathlib import Path
import pandas as pd


def extension_from_input(file_name) -> str:
    if hasattr(file_name, "name") and file_name.name:
        return Path(str(file_name.name)).suffix.lower()
    if isinstance(file_name, str):
        return Path(file_name).suffix.lower()
    return ""


def read_input(file_name) -> pd.DataFrame:
    ext = extension_from_input(file_name)
    if ext == ".csv":
        return pd.read_csv(file_name)
    if ext in {".xlsx", ".xls"}:
        return pd.read_excel(file_name)

    if isinstance(file_name, (bytes, bytearray)):
        raw = bytes(file_name)
        try:
            return pd.read_csv(io.BytesIO(raw))
        except Exception:
            return pd.read_excel(io.BytesIO(raw))

    raise ValueError("Unsupported file type. Upload CSV or XLSX.")
