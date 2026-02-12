import pandas as pd
from pathlib import Path
import openpyxl # needed for excel file -> df

def process_data(file_name, save_as_csv=False):
    """
    Processing .xlsx, .xls, and .csv files into Pandas Dataframe

    This should work for Excel files with multiple sheets
    
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

                # Change name of first column to "Sample Name"
                cols = list(df.columns)
                cols[0] = 'Sample Name'
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
                    flat_name = f"{parent}_{child}"
                    flat_columns.append(flat_name)

                # assign to the df columns
                df.columns = flat_columns

                # Create a copy of current columns as a list
                cols = list(df.columns)

                # Change the first element
                cols[0] = 'Sample Name'

                # Assign the modified list back
                df.columns = cols

            # Drop fully empty rows and columns
            df = df.dropna(axis=0, how="all")
            df = df.dropna(axis=1, how="all")

            parsed.append(df)
            
        merged_df = pd.concat(parsed, ignore_index=True)

        if save_as_csv:
            merged_df.to_csv(f"{file_name}.csv", index=False)

        return merged_df

    else:
        raise ValueError("Must be a CSV or Excel filetype. Please save and re-upload.")

#TODO: This is the main part that needs work, I barely touched it. I commented my ideas/thoughts below
def standardize_data(dataframe):
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

    # TODO: need to add a function to name the unnamed well column

    # TODO: need to figure out what to do about all of the unnamed columns

    # Add a reaction type column to distinguish which reaction we're looking at
    # TODO: NEED TO FIGURE OUT HOW TO MAKE THIS WORK FOR MORE DATA, might need to have a section where the 
    # scientist adds in the name of the reaction so that we can parse it out unless there's some sort of standard...
    # right now, to me, it seems like we could parse everything to do the LEFT of last dash (but idk if this will work forever)
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

if __name__=="__main__":
    # this section works
    df_csv = process_data("./data/Example_Data_SpiroXantPhos.csv") # this works!
    standardize_data(df_csv)

    # this shows how a df is created for an Excel file where both sheets do not match
    df_excel_diff_sheets = process_data("./data/Example_ChemStation_Data_NB-0123-0002.xlsx", True)

    # this shows how a df is created for an Excel file where the sheets do match
    df_excel = process_data("./data/Example_ChemStation_Data_GPT.xlsx", True)
