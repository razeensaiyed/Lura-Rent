import pandas as pd
import re

# -----------------------------
# 1. LOAD DATASET
# -----------------------------
df = pd.read_csv("raw_tenancy_dataset.csv")
print("Original rows:", len(df))

# -----------------------------
# 2. CLAUSE CLEANING FUNCTION
# -----------------------------
def is_clean_clause(text):
    if pd.isna(text):
        return False

    text = str(text).strip()
    lower = text.lower()
    words = text.split()

    # remove too short / too long
    if len(words) < 8:   # ✅ lowered minimum from 12 to 8
        return False
    if len(words) > 150: # ✅ raised maximum from 120 to 150
        return False

    # remove headings
    if lower.startswith(("section", "chapter", "part")):
        return False

    # remove fragments
    if re.match(r'^(and|or)\b', lower):
        return False
    if re.match(r'^\([a-z]\)', lower):       # (a), (b) etc.
        return False
    if re.match(r'^\([ivxlcdm]+\)', lower):  # (i), (ii) etc.
        return False

    # remove form fields
    form_words = [
        "mobile number","email id","e-mail","signature",
        "address of","description of premises","name of landlord",
        "name of tenant","schedule","form"
    ]
    for word in form_words:
        if word in lower:
            return False

    # remove blank template lines
    if "____" in text:
        return False

    # remove page markers
    if "page" in lower and "of" in lower:
        return False

    # remove act intro
    if "short title" in lower:
        return False

    return True

# -----------------------------
# 3. APPLY CLEANING
# -----------------------------
df["keep"] = df["clause"].apply(is_clean_clause)
clean_df = df[df["keep"] == True].copy()

# -----------------------------
# 4. REMOVE DUPLICATES
# -----------------------------
clean_df = clean_df.drop_duplicates(subset="clause").reset_index(drop=True)

print("Clean clauses:", len(clean_df))

# -----------------------------
# 5. SAVE DATASET
# -----------------------------
clean_df = clean_df.drop(columns=["keep"])
clean_df.to_csv("clean_tenancy_dataset.csv", index=False)

print("Saved dataset: clean_tenancy_dataset.csv")