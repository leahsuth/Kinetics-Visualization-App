import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def graphing(file_name):
  df = pd.read_csv(file_name)
  reaction = df["reaction_type"].iloc[0]

  plt.figure(figsize=(7, 4))
  ax = sns.scatterplot(data=df, x='time', y="concentration", hue='molecule')

  ax.set_xlabel("Time")
  ax.set_ylabel("Concentration (mM)")
  ax.set_title(f"Reaction ID: {reaction}")
  ax.legend()
  plt.tight_layout()
  plt.savefig(f"Reaction ID: {reaction}")
  plt.show()

graphing("NB-116.csv")
graphing("NB-121.csv")
graphing("NB-123.csv")
graphing("NB-124.csv")
graphing("NB-125.csv")
graphing("NB-150.csv")
graphing("NB-154.csv")

# need to know which molecules to graph, we could probably pass them in as parameters

