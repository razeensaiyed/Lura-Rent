import pandas as pd
from transformers import pipeline

# Load dataset
df = pd.read_csv("clean_tenancy_dataset.csv")
print("Clauses loaded:", len(df))

# Use a lighter model for testing
explainer = pipeline("text2text-generation", model="google/flan-t5-base")

def explain_clause(clause):
    prompt = f"Explain this tenancy law clause in simple language:\n\n{clause}"
    response = explainer(prompt, max_new_tokens=150)
    return response[0]["generated_text"].strip()

# Generate explanations
df["explanation"] = [explain_clause(c) for c in df["clause"]]

# Save dataset
df.to_csv("tenancy_finetune_dataset.csv", index=False)
print("Dataset saved: tenancy_finetune_dataset.csv")