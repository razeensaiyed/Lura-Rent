import pandas as pd
from transformers import pipeline

# ---------------------------
# 1. LOAD CLEAN DATASET
# ---------------------------
df = pd.read_csv("clean_tenancy_dataset.csv")
print("Clauses loaded:", len(df))

# ---------------------------
# 2. LOAD HUGGING FACE MODEL
# ---------------------------
# You can swap the model for smaller ones if system resources are limited
explainer = pipeline("text-generation", model="mistralai/Mistral-7B-Instruct-v0.2")

# ---------------------------
# 3. EXPLANATION FUNCTION
# ---------------------------
def explain_clause(clause):
    prompt = f"""
    Explain the following tenancy law clause in very simple language
    so that a common person can understand it.

    Legal clause:
    {clause}

    Simple explanation:
    """
    response = explainer(prompt, max_new_tokens=200, temperature=0.2)
    # Extract only the explanation part
    return response[0]["generated_text"].split("Simple explanation:")[-1].strip()

# ---------------------------
# 4. GENERATE EXPLANATIONS
# ---------------------------
explanations = []
for i, clause in enumerate(df["clause"]):
    print("Processing:", i+1)
    try:
        exp = explain_clause(clause)
    except Exception as e:
        print("Error:", e)
        exp = "Explanation generation failed"
    explanations.append(exp)

df["explanation"] = explanations

# ---------------------------
# 5. ADD TRAINING QUESTION
# ---------------------------
df["question"] = "Explain this tenancy law clause in simple language."

# ---------------------------
# 6. FINAL DATASET
# ---------------------------
final_df = df[["question","clause","explanation","section","source_pdf"]]

# ---------------------------
# 7. SAVE
# ---------------------------
final_df.to_csv("tenancy_finetune_dataset.csv", index=False)
print("Dataset saved: tenancy_finetune_dataset.csv")