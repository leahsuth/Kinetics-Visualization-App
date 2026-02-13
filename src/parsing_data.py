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
    file_name : str
        Path to file name containing data
    save_as_csv : bool
        Saves as CSV if True
    
    Returns
    --------
    df : pandas dataframe
        Dataframe with data from provided file
    """
    ext = Path(file_name).suffix.lower() # extract file type
    if ext == ".csv":
        # so far, if CSV, no processing needed to create dataframe
        df = pd.read_csv(file_name)

        # Change name of first column to "Sample Name"
        cols = list(df.columns)
        cols[0] = 'Sample Name'
        df.columns = cols

        if save_as_csv:
            df.to_csv(f"{file_name}.csv", index=False)
        
        return df

    elif ext in (".xlsx", ".xls"):
        # first, need to get the total number of sheets in the Excel file
        xls = pd.ExcelFile(file_name)
        num_sheets = len(xls.sheet_names)

        # Store all of the dataframes from Excel file in parsed
        parsed = []

        # process all of the sheets
        for i in range(num_sheets):
            # Read data into basic dataframe
            raw = pd.read_excel(file_name, sheet_name=i, header=None)

            # Find the first row that contains "Peak RT"
            matches = raw.index[raw.apply(lambda r: r.astype(str).str.contains("Peak RT", na=False).any(), axis=1)]

            # if not data from chemstation, may not have this column
            if len(matches) == 0:
                df = pd.read_excel(file_name, sheet_name=i)

                # Change name of first column to "Reaction"
                cols = list(df.columns)
                cols[0] = 'Reaction'
                df.columns = cols

            else:
                # header row is the one with the RT, above the Peak RT row
                hdr1_row = matches[0] - 1

                # Re-read sheet with multi-row header (RT, Peak Area/etc.)
                df = pd.read_excel(
                    file_name,
                    sheet_name=i,
                    skiprows=int(hdr1_row),
                    header=[0, 1]
                )

                # Extract the two header levels
                level0 = df.columns.get_level_values(0)
                level1 = df.columns.get_level_values(1)

                # Convert level 0 to Series so we can forward-fill merged cells
                level0_filled = pd.Series(level0).ffill()

                # Rebuild the MultiIndex using level 0
                df.columns = pd.MultiIndex.from_arrays([level0_filled, level1])

                # Now flatten the MultiIndex into single-level column names
                flat_columns = []
                for parent, child in df.columns:
                    flat_name = f"{parent}__{child}" # parse by __
                    flat_columns.append(flat_name)

                # assign to the df columns
                df.columns = flat_columns

            # Drop fully empty rows and columns
            df = df.dropna(axis=0, how="all")
            df = df.dropna(axis=1, how="all")

            parsed.append(df)

            # Create a copy of current columns as a list
            cols = list(df.columns)

            # Change the known columns
            cols[0] = 'Reaction'
            cols[1] = 'Well' # may need to be split up
            cols[2] = 'Injection_Numbers'

            # Assign the modified list back
            df.columns = cols

            # Create a new column for Plate Number, defaults to AAA
            new_col = df["Well"].where(df["Well"].str.contains("-"),"AAA").str.split("-").str[0]
            df.insert(1, "Plate_Number", new_col)

            # Remove Plate_Number- from Well if it exists
            df["Well"] = df["Well"].str.replace(r"^.*?-", "", regex=True)

            df["Sheet_Number"] = i

        merged_df = pd.concat(parsed, ignore_index=True)

        if save_as_csv:
            merged_df.to_csv(f"{file_name}.csv", index=False)

        return merged_df

    else:
        raise ValueError("Must be a CSV or Excel filetype. Please save and re-upload.")

#TODO: This is the main part that needs work, I barely touched it. I commented my ideas/thoughts below
def standardize_data_mockdata(dataframe):
    """
    Standardize data function
    Process the Dataframe for graphing

    Parameters
    -----------
    dataframe : pd dataframe
        Pandas Dataframe to be processed
    
    Returns
    --------
    df : pandas dataframe
        Saves multiple CSV files of pandas dataframe
        One CSV file is saved per experiment
    """
    # THIS CURRENTLY ONLY WORKS FOR THE CSV MOCK DATA

    # standardize column titles
    dataframe.columns = dataframe.columns.str.strip().str.lower().str.replace(' ', '_').str.strip()

    # TODO: need to figure out what to do about all of the unnamed columns

    # Add a reaction type column to distinguish which reaction we're looking at
    # TODO: now we don't have to do this... can assume that one data file only has one reaction
    dataframe["reaction_type"] = dataframe["sample_name"].str[:6] # this may not be consistent for future data!

    # pandas melt to make each concentration so each group has its own row for plotting
    # TODO: Need to make this work for other data
    melted_data = pd.melt(dataframe,
                        ["sample_name", "reaction_type", "time"],
                        ["amine", "aryl_bromide", "mono", "di_same_ring", "di_opposite_ring", "tri", "spiro", "unknown_rt_2.2"],
                        "molecule", "concentration")

    # printing to inspect
    # print(melted_data.head(50))

    # now, download the data!
    # should save in a folder later
    for reaction, group in melted_data.groupby("reaction_type"):
        group.to_csv(f"{reaction}.csv", index=False)

def standardize_data_realdata(dataframe, save_as_csv=False):
    """
    Standardize data function
    Process the Dataframe for graphing

    Parameters
    -----------
    dataframe : pd dataframe
        Pandas Dataframe to be processed
    rows : bool
        If time increases down the row
    cols : bool
        If time increases across columns
    
    Returns
    --------
    df : pandas dataframe
        Saves multiple CSV files of pandas dataframe
        One CSV file is saved per experiment
    """
    # pandas melt to make each concentration so each group has its own row for plotting
    id_cols = ["Reaction", "Plate_Number", "Well", "Injection_Numbers"]

    if "Sheet_Number" in dataframe.columns:
        id_cols.append("Sheet_Number")

    melted_data = pd.melt(dataframe, id_vars=id_cols, var_name="Measurement", value_name="Value")

    # add a column for the reactant
    reactant_col = melted_data["Measurement"].str.extract(r"RT_(\d+\.?\d*)")[0].astype(str)
    melted_data.insert(3, "Reactant", reactant_col)

    # Add a new column for RT (not peak)
    rt_col = melted_data["Measurement"].str.extract(r"^(.*?)_RT_")[0]
    melted_data.insert(3, "RT", rt_col)
    #TODO: Filling missing RT with the RT Num for now...should figure out what to do
    melted_data["RT"] = melted_data["RT"].fillna(melted_data["Reactant"].astype(str))

    # Remove RT-#__ from Measurement
    melted_data["Measurement"] = melted_data["Measurement"].str.replace(r"^.*?__", "", regex=True)

    # convert to pivot table
    id_cols.append("Reactant")
    id_cols.append("RT")
    pivoted_data = melted_data.pivot(index=id_cols, columns='Measurement', values='Value').reset_index()

    # sort by Sheet Number, if it exists
    if "Sheet_Number" in pivoted_data.columns:
        pivoted_data = pivoted_data.sort_values(by=["Sheet_Number", 'Well'])

    # now, download the data!
    # should save in a folder later
    if save_as_csv:
        pivoted_data.to_csv("final_data.csv", index=False)
    return pivoted_data

def add_time(dataframe, row, col):
    """
    Standardize data function
    Process the Dataframe for graphing

    Parameters
    -----------
    dataframe : pd dataframe
        Pandas Dataframe to be processed
    rows : bool
        If time increases down the row
    cols : bool
        If time increases across columns
    
    Returns
    --------
    df : pandas dataframe
        Saves multiple CSV files of pandas dataframe
        One CSV file is saved per experiment
    """
    if row:
        mapping_wells = {"A" : 1,
                        "B" : 2,
                        "C" : 3,
                        "D" : 4,
                        "E" : 5,
                        "F" : 6,
                        "G" : 7,
                        "H" : 8}
        dataframe["Time"] = dataframe["Well"].str.extract(r"([A-H])")[0].map(mapping_wells)

    elif col:
        dataframe["Time"] = dataframe["Well"].str.extract(r"(\d+)").astype(int)

    else:
        raise ValueError("Cannot support this.")
        
    dataframe.to_csv("final_data.csv", index=False)

if __name__=="__main__":
    # this section works
    df_csv = process_data("./data/Example_Data_SpiroXantPhos.csv") # this works!
    #standardize_data_mockdata(df_csv)

    # this shows how a df is created for an Excel file with two sheets, but one experiment
    df_excel_diff_sheets = process_data("./data/Example_ChemStation_Data_GPT_TWOSHEETSONEEXPERIMENT.xlsx", True)
    df = standardize_data_realdata(df_excel_diff_sheets, False)
    add_time(df, False, True)

    # this shows how a df is created for an Excel file with just one sheet
    df_excel = process_data("./data/Example_ChemStation_Data_NB-0123-0002_ONESHEET.xlsx", True)
    #df = standardize_data_realdata(df_excel, False)
    #add_time(df, False, True)
