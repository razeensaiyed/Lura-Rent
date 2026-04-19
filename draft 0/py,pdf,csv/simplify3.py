import pandas as pd
import re

df = pd.read_csv("legal_tenancy_dataset_structured.csv")

def is_good_clause(text):

    if pd.isna(text):
        return False

    text = text.strip()

    # remove very short text
    if len(text.split()) < 10:
        return False

    # remove extremely long OCR garbage
    if len(text.split()) > 120:
        return False

    # remove section headings
    if re.match(r"^(section|chapter|part)", text.lower()):
        return False

    # remove fragments
    bad_patterns = [
        r"^\(", 
        r"^\d+\.", 
        r"^[ivxlcdm]+", 
        r"% per annum",
        r"date from which",
        r"act shall be called"
    ]

    for p in bad_patterns:
        if re.search(p, text.lower()):
            return False

    return True


df["clean"] = df["clause"].apply(is_good_clause)

clean_df = df[df["clean"] == True].copy()

clean_df = clean_df.drop_duplicates(subset="clause")

print("Original:", len(df))
print("Clean clauses:", len(clean_df))

clean_df.to_csv("tenancy_clean_dataset.csv", index=False)