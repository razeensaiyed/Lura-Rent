import pandas as pd
import re
import os
import pdfplumber
import string

# -------------------------------------------------
# 1. Hardcoded PDF list
# -------------------------------------------------

pdf_files = [
    "Model-Tenancy-Act-English-02_06_2021.pdf",
    "eng_maharashtra_rent_control_ac.pdf",
]

# -------------------------------------------------
# 2. Keyword Filters
# -------------------------------------------------

tenancy_keywords = [

# core parties
"tenant",
"landlord",
"lessor",
"lessee",

"licensee",
"license fee",
"leave and licence",
"permitted increase",
"standard rent",
"lodging house",
"tenant in occupation",

# property
"premises",
"dwelling",
"building",
"house",
"flat",
"apartment",
"property",

# agreements
"tenancy",
"lease",
"tenancy agreement",
"lease agreement",
"rent agreement",
"leave and license",
"lease deed",

# rent related
"rent",
"rent payable",
"rent payment",
"rent increase",
"rent revision",
"arrears of rent",
"standard rent",
"fair rent",
"enhanced rent",

# eviction / possession
"eviction",
"evict",
"recovery of possession",
"possession of premises",
"vacate",
"ejectment",
"unlawful occupation",

# deposits / payments
"security deposit",
"deposit",
"advance rent",

# rights and duties
"rights of tenant",
"rights of landlord",
"obligations",
"duties",
"responsibility",
"consent",

# dispute resolution
"rent authority",
"rent court",
"rent tribunal",
"appeal",
"application",
"order",
"dispute",

# termination
"termination",
"termination of tenancy",
"termination of lease",
"expiry of tenancy",

# property management
"sublet",
"sub lease",
"sub tenancy",
"property manager",
"rental agent",
"broker",

# law references
"rent control",
"maharashtra rent control act",
"model tenancy act"
]

bad_keywords = [
    "criminal","murder","terror","dowry","trademark",
    "copyright","patent","income tax","gst","divorce",
    "marriage","succession","adoption"
]

tenancy_pattern = re.compile(r'\b(' + '|'.join(map(re.escape, tenancy_keywords)) + r')\b', re.IGNORECASE)
bad_pattern = re.compile(r'\b(' + '|'.join(map(re.escape, bad_keywords)) + r')\b', re.IGNORECASE)

# -------------------------------------------------
# 3. Text Normalization
# -------------------------------------------------

def normalize(text):

    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    text = re.sub(r'\s+', ' ', text).strip()

    return text


# -------------------------------------------------
# 4. Check if clause is relevant
# -------------------------------------------------

def is_valid_clause(text):

    if len(text.split()) < 12:
        return False

    if bad_pattern.search(text):
        return False

    if tenancy_pattern.search(text):
        return True

    return False


# -------------------------------------------------
# 5. Clause Extraction with Section Tracking
# -------------------------------------------------

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

            # detect section titles
            section_match = re.findall(r'Section\s+\d+[A-Za-z\-]*', text)

            if section_match:
                current_section = section_match[0]

            # better splitting
            parts = re.split(r'\(\d+\)|\([a-z]\)', text)

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


# -------------------------------------------------
# 6. Extract From All PDFs
# -------------------------------------------------

all_clauses = []

for pdf in pdf_files:

    extracted = extract_clauses_from_pdf(pdf)

    print(pdf, "→", len(extracted), "clauses")

    for clause in extracted:

        clause["source_pdf"] = pdf
        all_clauses.append(clause)


print("\nTotal extracted clauses:", len(all_clauses))


# -------------------------------------------------
# 7. Create Dataset
# -------------------------------------------------

df = pd.DataFrame(all_clauses)

# remove duplicates
df = df.drop_duplicates(subset="clause").reset_index(drop=True)

print("Final dataset size:", df.shape)


# -------------------------------------------------
# 8. Generate Better Questions
# -------------------------------------------------

questions = [
    "Explain this tenancy law clause.",
    "What does this clause mean in simple terms?",
    "Summarize this legal clause.",
    "Simplify this tenancy law provision."
]

df["question"] = [questions[i % len(questions)] for i in range(len(df))]
df.rename(columns={"clause":"answer"}, inplace=True)


# -------------------------------------------------
# 9. Save Dataset
# -------------------------------------------------

df.to_csv("legal_tenancy_dataset_structured.csv", index=False)

print("Dataset saved as legal_tenancy_dataset_structured.csv")


# -------------------------------------------------
# 10. Interactive Search
# -------------------------------------------------

df["normalized"] = df["answer"].apply(normalize)

print("\nInteractive clause search (type 'exit' to quit)")

while True:

    query = input("\nEnter clause keywords: ").strip()

    if query.lower() == "exit":
        break

    q_norm = normalize(query)
    words = q_norm.split()

    results = df[
        df["normalized"].apply(lambda x: sum(word in x for word in words) >= 2)
    ]

    if results.empty:
        print("No clause found.")

    else:
        print("\nMatches found:\n")

        for _, row in results.head(10).iterrows():

            print("-", row["answer"])
            print("  Section:", row["section"], "| Page:", row["page"], "| Source:", row["source_pdf"])
            print()