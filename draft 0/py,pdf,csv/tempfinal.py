import pandas as pd

df = pd.read_csv("tenancy_clean_dataset.csv")

print(df["source_pdf"].value_counts())