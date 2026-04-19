import pandas as pd
import re
import random

# ------------------------------
# 1 Load dataset
# ------------------------------

df = pd.read_csv("legal_tenancy_dataset_structured.csv")

# ------------------------------
# 2 Cleaning
# ------------------------------

def clean_clause(text):

    text = str(text)

    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    return text


df["answer"] = df["answer"].apply(clean_clause)

# remove very short clauses
df = df[df["answer"].str.split().str.len() > 10]

# remove extremely long clauses
df = df[df["answer"].str.split().str.len() < 120]

# remove obvious fragments
df = df[~df["answer"].str.contains(r'^\(|^\[', regex=True)]

# ------------------------------
# 3 Instruction Templates
# ------------------------------

explain_templates = [
"Explain the following tenancy law clause in simple terms.",
"Interpret this legal clause related to tenancy law.",
"Simplify the following tenancy law provision."
]

summary_templates = [
"Summarize the following tenancy law clause.",
"Provide a short summary of this legal provision."
]

classification_templates = [
"Identify the legal topic of the following clause."
]

# ------------------------------
# 4 Generate Training Samples
# ------------------------------

dataset = []

for _, row in df.iterrows():

    clause = row["answer"]
    section = row["section"]
    source = row["source_pdf"]

    # explanation task
    dataset.append({
        "instruction": random.choice(explain_templates),
        "input": clause,
        "output": clause,
        "section": section,
        "source": source
    })

    # summarization task
    dataset.append({
        "instruction": random.choice(summary_templates),
        "input": clause,
        "output": clause,
        "section": section,
        "source": source
    })

    # classification task
    topic = "tenancy law"

    dataset.append({
        "instruction": random.choice(classification_templates),
        "input": clause,
        "output": topic,
        "section": section,
        "source": source
    })

# ------------------------------
# 5 Convert to DataFrame
# ------------------------------

ft_df = pd.DataFrame(dataset)

# remove duplicates
ft_df = ft_df.drop_duplicates()

# ------------------------------
# 6 Dataset Validation
# ------------------------------

ft_df = ft_df.dropna()

ft_df = ft_df[
    (ft_df["instruction"].str.len() > 5) &
    (ft_df["input"].str.len() > 10) &
    (ft_df["output"].str.len() > 3)
]

# ------------------------------
# 7 Save Dataset
# ------------------------------

ft_df.to_csv("tenancy_finetune_dataset.csv", index=False)

print("Fine-tuning dataset created")
print("Total samples:", len(ft_df))

print(ft_df.sample(10))