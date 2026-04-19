import pandas as pd

df = pd.read_csv("legal_tenancy_dataset_structured.csv")

topics = {
    "rent": ["rent"],
    "eviction": ["evict","eviction"],
    "tenant": ["tenant"],
    "landlord": ["landlord"],
    "deposit": ["deposit","security deposit"],
    "lease": ["lease"],
    "premises": ["premises"],
    "rent court": ["rent court","rent tribunal"],
}

for topic, words in topics.items():
    
    count = df["answer"].str.contains("|".join(words), case=False).sum()
    
    print(topic, ":", count)

print(df["section"].value_counts().head(20))

df["length"] = df["answer"].apply(lambda x: len(x.split()))

print(df["length"].describe())

duplicates = df[df.duplicated(subset="answer", keep=False)]
print(len(duplicates))

print(df.sample(20)["answer"])

print(df["source_pdf"].value_counts())

df[df["answer"].str.contains("eviction", case=False)].head(10)

from collections import Counter

words = " ".join(df["answer"]).lower().split()

common = Counter(words).most_common(30)

print(common)