"""
Parse kinetics data from CSV and Excel (ChemStation) files.
Excel support requires openpyxl (for .xlsx) and xlrd (for .xls).
"""
import pandas as pd
from pathlib import Path
import openpyxl # needed for excel file -> df 

#TODO: Need to add a section that just processes the first line of the Excel file for the description

def process_data(file_name, save_as_csv=False):
    """
    Processing .xlsx, .xls, and .csv files into Pandas Dataframe

    This should work for Excel files with multiple sheets
    Based on Merck feedback, assuming that multiple sheets correspond to the same reaction name
    #TODO: Need to add that to the Streamlit home page

    Parameters
    -----------
    file_name : str or file-like
        Path to file or Streamlit UploadedFile (must have .name for extension)
    save_as_csv : bool
        Saves as CSV if True
    Returns
    --------
    df : pandas dataframe
        Dataframe with data from provided file
    """
    # Handle both file paths and uploaded file
    ext = Path(file_name.name).suffix.lower() if hasattr(file_name, "name") else Path(file_name).suffix.lower()
    out_path = Path(getattr(file_name, "name", file_name)).with_suffix(".csv") if save_as_csv else None

    if ext == ".csv":
        #so far, if CSV, no processing needed to create dataframe
        df = pd.read_csv(file_name)
        cols = list(df.columns)
        #change name of first column to Sample Name
        cols[0] = "Sample Name"
        df.columns = cols
        if save_as_csv:
            df.to_csv(out_path, index=False)
        return df

    elif ext in (".xlsx", ".xls"):
        #first, need to get the total number of sheets in the Excel file
        engine = "openpyxl" if ext == ".xlsx" else "xlrd"
        xls = pd.ExcelFile(file_name, engine=engine)
        num_sheets = len(xls.sheet_names)
        #store all of the dataframes from Excel file in parsed
        parsed = []
    
        #process all of the sheet
        for i in range(num_sheets):
            #read data into basic dataframe
            raw = pd.read_excel(file_name, sheet_name=i, header=None, engine=engine)
            #find the first row that contains "Peak RT"
            matches = raw.index[raw.apply(lambda r: r.astype(str).str.contains("Peak RT", na=False).any(), axis=1)]
            #if not data from chemstation, may not have this column
            if len(matches) == 0:
                df = pd.read_excel(file_name, sheet_name=i, engine=engine)
                #change name of first column to Reaction
                cols = list(df.columns)
                cols[0] = "Reaction"
                df.columns = cols
            else:
                #header row is the one with the RT, above the peak RT row
                hdr1_row = matches[0] - 1
                #Re-read sheet with multi-row header (RT, Peak Area/etc.)
                df = pd.read_excel(
                    file_name,
                    sheet_name=i,
                    skiprows=int(hdr1_row),
                    header=[0, 1],
                    engine=engine,
                )
                level0 = df.columns.get_level_values(0)
                level1 = df.columns.get_level_values(1)
                # Extract the two header levels
                level0_filled = pd.Series(level0).ffill()
                # Rebuild the MultiIndex using level 0
                df.columns = pd.MultiIndex.from_arrays([level0_filled, level1])
                # Now flatten the MultiIndex into single-level column names
                flat_columns = []
                for parent, child in df.columns:
                    flat_columns.append(f"{parent}__{child}")
                df.columns = flat_columns
            #drop any rows or columns that are empty
            df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
            parsed.append(df)
            ## Create a copy of current columns as a list
            cols = list(df.columns)
            # Change the known columns
            cols[0] = "Reaction"
            cols[1] = "Well"
            cols[2] = "Injection_Numbers"
            # Assign the modified list back
            df.columns = cols
            # Create a new column for Plate Number, defaults to AAA
            new_col = df["Well"].where(df["Well"].str.contains("-"), "AAA").str.split("-").str[0]
            df.insert(1, "Plate_Number", new_col)
            # Remove Plate_Number- from Well if it exists
            df["Well"] = df["Well"].str.replace(r"^.*?-", "", regex=True)
            df["Sheet_Number"] = i

        merged_df = pd.concat(parsed, ignore_index=True)
        if save_as_csv:
            merged_df.to_csv(out_path, index=False)
        return merged_df

    else:
        raise ValueError("Must be a CSV or Excel filetype. Please save and re-upload.")

def standardize_data(df, save_as_csv=False):
    #get metadata columns
    id_cols = ["Reaction", "Plate_Number", "Well", "Injection_Numbers"]
    #if sheet number is in the columns, add it to the metadata columns
    if "Sheet_Number" in df.columns:
        id_cols.append("Sheet_Number")
    #melt the data into a long format
    melted_data = pd.melt(df, id_vars=id_cols, var_name="Measurement", value_name="Value")
    #extract the reactant column
    reactant_col = melted_data["Measurement"].str.extract(r"RT_(\d+\.?\d*)")[0].astype(str)
    #insert the reactant column into the dataframe
    melted_data.insert(3, "Reactant", reactant_col)
    #extract the RT column
    rt_col = melted_data["Measurement"].str.extract(r"^(.*?)_RT_")[0]
    #insert the RT column into the dataframe
    melted_data.insert(3, "RT", rt_col)
    #fill any missing RT values with the reactant column
    melted_data["RT"] = melted_data["RT"].fillna(melted_data["Reactant"].astype(str))
    #remove the __ from the measurement column
    melted_data["Measurement"] = melted_data["Measurement"].str.replace(r"^.*?__", "", regex=True)

    # pivot_table handles duplicate index/column pairs
    pivot_index = id_cols + ["Reactant", "RT"]
    pivoted_data = melted_data.pivot_table(
        index=pivot_index, columns="Measurement", values="Value", aggfunc="first"
    ).reset_index()

    #sort the data by Sheet Number and Well
    if "Sheet_Number" in pivoted_data.columns:
        pivoted_data = pivoted_data.sort_values(by=["Sheet_Number", "Well"])
    if save_as_csv:
        pivoted_data.to_csv("final_data.csv", index=False)
    return pivoted_data

#add time column from Well: row=True uses letter (A=1..H=8), col=True uses number.
def add_time(df, row, col):
    if row:
        wells = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8}
        #extract the letter from the Well column and map to the number
        df["Time"] = df["Well"].str.extract(r"([A-H])")[0].map(wells)
    elif col:
        #convert number from well column to time
        df["Time"] = df["Well"].str.extract(r"(\d+)").astype(int)
    else:
        raise ValueError("Must specify row=True or col=True for time extraction.")
    df.to_csv("final_data.csv", index=False)


if __name__ == "__main__":
    df_csv = process_data("./data/Example_Data_SpiroXantPhos.csv")
    df_excel_diff_sheets = process_data("./data/Example_ChemStation_Data_GPT_TWOSHEETSONEEXPERIMENT.xlsx", True)
    df = standardize_data(df_excel_diff_sheets, False)
    add_time(df, False, True)
    df_excel = process_data("./data/Example_ChemStation_Data_NB-0123-0002_ONESHEET.xlsx", True)