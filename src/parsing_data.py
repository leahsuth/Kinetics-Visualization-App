import pandas as pd

# Mapping (matches the paper)
# this wasn't used, but keeping it in case
mol_map = {"amine" : "1",
            "aryl_bromide" : "2",
            "mono" : "3",
            "di_same_ring" : "4a",
            "di_opposite_ring" : "4b",
            "tri" : "5",
            "spiro" : "6",
            "unknown_rt_2.2" : "unknown"}

# Create a pandas dataframe with all of the data
mock_data = pd.read_csv("./data/Example_Data_SpiroXantPhos.csv")

# standardize column titles
mock_data.columns = mock_data.columns.str.strip().str.lower().str.replace(' ', '_').str.strip()

# Add a reaction type column to distinguish which reaction we're looking at
mock_data["reaction_type"] = mock_data["sample_name"].str[:6] # this may not be consistent for future data!

# pandas melt to make each concentration so each group has its own row for plotting
melted_data = pd.melt(mock_data,
                      ["sample_name", "reaction_type", "time"],
                      ["amine", "aryl_bromide", "mono", "di_same_ring", "di_opposite_ring", "tri", "spiro", "unknown_rt_2.2"],
                      "molecule",
                      "concentration")

# Converting negative values to zero
melted_data["concentration"] = melted_data["concentration"].clip(lower=0)

# printing to inspect
#print(melted_data.head(50))

# now, download the data!
# should save in a folder later
for reaction, group in melted_data.groupby("reaction_type"):
    group.to_csv(f"{reaction}.csv", index=False)

# Parsing through values to determine validity
# 1. Get rid of negative values? For now, converting to 0.
# 2. Is there some sort of threshold that we can consider as 0?
# What do we do when there is data missing? -> We could infer missing values? (mean/median)
# We need some sort of data validation pipeline here to make sure only valid data is considered. we also need to figure out what the definition of valid data is

