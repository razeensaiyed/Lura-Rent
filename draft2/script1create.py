import pdfplumber
import re
import os
import string
import pandas as pd
# -------------------------------
# 1. PDF Sources
# -------------------------------
pdf_files = [
    "Model-Tenancy-Act-English-02_06_2021.pdf",
    "eng_maharashtra_rent_control_ac.pdf",
]

# -------------------------------
# 2. Keyword Filters
# -------------------------------
tenancy_keywords = [
    "tenant","landlord","lease","rent","rental","premises",
    "eviction","tenancy","security deposit","rent control",
    "rent increase","lease termination","leave and license"
]

bad_keywords = [
    "criminal","murder","terror","dowry","trademark",
    "copyright","patent","income tax","gst","divorce",
    "marriage","succession","adoption"
]

tenancy_pattern = re.compile(r'\b(' + '|'.join(map(re.escape, tenancy_keywords)) + r')\b', re.IGNORECASE)
bad_pattern = re.compile(r'\b(' + '|'.join(map(re.escape, bad_keywords)) + r')\b', re.IGNORECASE)

# -------------------------------
# 3. Text Normalization
# -------------------------------
def normalize(text):
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# -------------------------------
# 4. Check if clause is relevant
# -------------------------------
def is_valid_clause(text):
    words = text.split()
    if len(words) < 8:   # lowered minimum to catch short but valid clauses
        return False
    if len(words) > 150: # raised maximum for long provisions
        return False
    if bad_pattern.search(text):
        return False
    if tenancy_pattern.search(text):
        return True
    return False

# -------------------------------
# 5. Clause Extraction with Section Tracking
# -------------------------------
def extract_clauses_from_pdf(filename):
    clauses = []
    if not os.path.exists(filename):
        print("File not found:", filename)
        return clauses

    with pdfplumber.open(filename) as pdf:
        current_section = "Unknown"

        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if not text:
                continue
            text = text.replace("\n", " ")

            # detect section titles (expanded regex for variations)
            section_match = re.findall(r'(Section|Sec\.|S\.)\s+\d+[A-Za-z\-]*', text, re.IGNORECASE)
            if section_match:
                current_section = section_match[0]

            # split into clauses more accurately
            parts = re.split(r'(?<=[.;])\s+|(?<=Provided that)|(?<=Explanation)', text)

            for part in parts:
                part = part.strip()
                if part.isupper():
                    continue
                if re.match(r'^(CHAPTER|PART)', part, re.IGNORECASE):
                    continue
                if re.match(r'^\d+$', part):
                    continue
                if is_valid_clause(part):
                    clauses.append({
                        "clause": part,
                        "section": current_section,
                        "page": page_number
                    })

    return clauses

# -------------------------------
# 6. Extract from All PDFs
# -------------------------------
all_clauses = []

for pdf in pdf_files:
    extracted = extract_clauses_from_pdf(pdf)
    print(pdf, "→", len(extracted), "clauses")
    for clause in extracted:
        clause["source_pdf"] = pdf
        all_clauses.append(clause)

print("\nTotal extracted clauses:", len(all_clauses))

# -------------------------------
# 7. Create and Save Dataset
# -------------------------------
df = pd.DataFrame(all_clauses)

# remove duplicates
df = df.drop_duplicates(subset="clause").reset_index(drop=True)

print("Final dataset size:", df.shape)

df.to_csv("raw_tenancy_dataset.csv", index=False)
print("Dataset saved as raw_tenancy_dataset.csv")
