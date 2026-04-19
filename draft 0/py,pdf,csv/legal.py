import pandas as pd
import re
import os
import pdfplumber
import string

# -------------------------------------------------
# 0. Check files in current directory
# -------------------------------------------------
print("Files in directory:", os.listdir("."))

# -------------------------------------------------
# 1. Tenancy Keywords
# -------------------------------------------------
tenancy_keywords = [
    "tenant", "landlord", "lease", "rent", "rental",
    "lease agreement", "rent agreement", "eviction",
    "eviction notice", "tenancy agreement", "rent control",
    "rent control act", "rent increase", "security deposit",
    "tenant rights", "landlord rights", "lease termination",
    "tenancy termination", "rent dispute", "rent arrears",
    "eviction order", "tenant protection", "leave and license",
    "maharashtra rent control act", "model tenancy act",
    "premises", "demised premises", "lease deed", "tenancy deed"
]

bad_keywords = [
    "criminal", "murder", "terror", "terrorism",
    "divorce", "marriage", "dowry",
    "trademark", "copyright", "patent",
    "defamation", "cheque bounce",
    "income tax", "gst",
    "property inheritance", "succession",
    "adoption", "family settlement",
    "alms", "begging", "unlawful assembly", "arrest", "section 153a"
]

# -------------------------------------------------
# 2. Filtering Functions
# -------------------------------------------------
def contains_bad(text):
    if pd.isna(text):
        return False
    text_lower = text.lower()
    return any(bk in text_lower for bk in bad_keywords)

def contains_tenancy(text):
    if pd.isna(text):
        return False
    text_lower = text.lower()
    if contains_bad(text_lower):
        return False
    return any(k in text_lower for k in tenancy_keywords)

# -------------------------------------------------
# 3. Load PDF Clauses
# -------------------------------------------------
def load_pdf_clauses(filename):

    clauses = []

    if not os.path.exists(filename):
        return clauses

    with pdfplumber.open(filename) as pdf:

        for page in pdf.pages:

            text = page.extract_text()

            if text:

                # remove line breaks
                text = text.replace("\n", " ")

                # split into sentences
                sentences = re.split(r'(?<=[.!?])\s+', text)

                for sent in sentences:

                    sent = sent.strip()

                    # ignore headings
                    if sent.isupper():
                        continue

                    if re.match(r'^(CHAPTER|SECTION|PART)', sent, re.IGNORECASE):
                        continue

                    # ignore short fragments
                    if len(sent.split()) < 12:
                        continue

                    # keep only tenancy related clauses
                    if contains_tenancy(sent):
                        clauses.append(sent)

    return clauses

# Add current PDFs only; you can append more later
pdf_files = [
    "Model-Tenancy-Act-English-02_06_2021.pdf",
    "eng_maharashtra_rent_control_ac.pdf",
    "docum.pdf",
    "legaldoc.pdf"
]

pdf_clauses = []
pdf_sources = []

for pf in pdf_files:
    pdf_parts = load_pdf_clauses(pf)
    for clause in pdf_parts:
        pdf_clauses.append(clause)
        pdf_sources.append(f"PDF:{pf}")

print("PDF rental clauses before cleaning:", len(pdf_clauses))

# -------------------------------------------------
# 4. Clean Clauses
# -------------------------------------------------
clean_clauses = []
clean_sources = []

for clause, src in zip(pdf_clauses, pdf_sources):
    clause = re.sub(r"^\d+\.", "", clause)           # Remove numbering
    clause = re.sub(r"^[o\-•]", "", clause)         # Remove bullets
    clause = clause.strip()
    
    # Remove chapter/section headings
    if re.match(r'^(CHAPTER|SECTION|PART)\s+[IVX0-9]+', clause, re.IGNORECASE):
        continue
    
    if len(clause.split()) > 6:  # keep meaningful clauses only
        clean_clauses.append(clause)
        clean_sources.append(src)

# -------------------------------------------------
# 5. Create Final Dataset with Question Column
# -------------------------------------------------
final_df = pd.DataFrame({
    "question": ["Simplify this clause"] * len(clean_clauses),
    "answer": clean_clauses,
    "source": clean_sources
})

# -------------------------------------------------
# 6. Remove duplicates
# -------------------------------------------------
final_df = final_df.drop_duplicates(subset="answer").reset_index(drop=True)
print("Final rental dataset size after deduplication:", final_df.shape)

# -------------------------------------------------
# 7. Save Dataset
# -------------------------------------------------
final_df.to_csv("rental_legal_dataset.csv", index=False)
print("Dataset saved as rental_legal_dataset.csv")

# -------------------------------------------------
# 8. Show Sample
# -------------------------------------------------
print("\nSample clauses:\n")
for i in range(min(10, len(final_df))):
    print(i+1, ".", final_df.loc[i, "answer"], "| Source:", final_df.loc[i, "source"])

# -------------------------------------------------
# 9. Interactive Clause Query (fuzzy/partial match)
# -------------------------------------------------
def normalize(text):
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    text = re.sub(r'\s+', ' ', text).strip()
    return text

print("\n--- Interactive Clause Query ---")
print("Type a clause to search (or 'exit' to quit):")

while True:
    user_input = input("\nEnter clause: ").strip()
    if user_input.lower() in ["exit", "quit"]:
        break
    
    norm_input = normalize(user_input)
    
    # Find matching clauses
    matches = []
    for idx, row in final_df.iterrows():
        if any(word in normalize(row["answer"]) for word in norm_input.split()):
            matches.append(row)
    
    if len(matches) == 0:
        print("No matching clause found in dataset.")
    else:
        print(f"\nFound {len(matches)} matching clause(s):\n")
        for row in matches:
            print("-", row["answer"], "| Source:", row["source"])