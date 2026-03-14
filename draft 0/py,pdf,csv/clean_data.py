import pandas as pd
import re

# load dataset
df = pd.read_csv("legal_tenancy_dataset_structured.csv")

print("Original rows:", len(df))

def is_good_clause(text):

    # remove roman numeral fragments
    if re.match(r'^[IVXLCDM]+\b', text):
        return False

# remove act references
    if re.search(r'act\s+[ivxlcdm\d]+\s+of\s+\d{4}', text.lower()):
        return False

    if pd.isna(text):
        return False

    text = str(text).strip()

    # remove very short fragments
    if len(text.split()) < 10:
        return False

    # remove extremely long OCR junk
    if len(text.split()) > 120:
        return False

    # remove headings
    if re.match(r'^(section|chapter|part)', text.lower()):
        return False
    
    if "____" in text:
        return False

    # remove common OCR garbage
    bad_patterns = [
        r"date from which",
        r"act shall be called",
        r"^\(",
        r"^\d+\."
    ]

    if "page" in text.lower() and "of" in text.lower():
        return False

    for p in bad_patterns:
        if re.search(p, text.lower()):
            return False

    form_patterns = [
    "mobile number",
    "email id",
    "e-mail id",
    "description of premises",
    "form",
    "schedule",
    "name of landlord",
    "name of tenant",
    "address of",
    "signature",
    "date:",
    "place:",
    "details of",
]
    for p in form_patterns:
        if p in text.lower():
            return False

    return True


# apply cleaning
df["clean"] = df["answer"].apply(is_good_clause)

clean_df = df[df["clean"] == True].copy()

# remove duplicates
clean_df = clean_df.drop_duplicates(subset="answer")

print("Clean clauses:", len(clean_df))

# save
clean_df.to_csv("tenancy_clean_dataset.csv", index=False)

print("Saved as tenancy_clean_dataset.csv")

print(clean_df["answer"].sample(10))