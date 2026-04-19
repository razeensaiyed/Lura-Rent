import pandas as pd

# -----------------------------
# 1. LOAD DATASET
# -----------------------------

df = pd.read_csv("tenancy_finetune_dataset.csv")

print("Rows loaded:", len(df))


# -----------------------------
# 2. CREATE TRAINING PROMPT
# -----------------------------

def build_prompt(row):

    instruction = "Explain the following tenancy law clause in simple language."

    input_text = row["clause"]

    output_text = row["explanation"]

    return pd.Series([instruction, input_text, output_text])


df[["instruction","input","output"]] = df.apply(build_prompt, axis=1)


# -----------------------------
# 3. FINAL DATASET STRUCTURE
# -----------------------------

train_df = df[[
    "instruction",
    "input",
    "output",
    "section",
    "source_pdf"
]]


# -----------------------------
# 4. SAVE DATASET
# -----------------------------

train_df.to_csv("tenancy_training_dataset.csv", index=False)

print("Final dataset saved: tenancy_training_dataset.csv")


# -----------------------------
# 5. QUICK SAMPLE CHECK
# -----------------------------

print("\nSample rows:\n")
print(train_df.sample(5))