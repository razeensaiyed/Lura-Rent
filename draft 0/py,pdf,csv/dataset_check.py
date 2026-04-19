import pandas as pd

df = pd.read_csv("tenancy_clean_dataset.csv")

clauses = df["answer"].str.lower()

phrases = [
"security deposit",
"rent court",
"rent tribunal",
"recovery of possession",
"leave and license"
]

keywords = [

# core tenancy terms
"tenant",
"landlord",
"tenancy",
"lease",
"rent",
"rental",
"premises",

# agreements
"tenancy agreement",
"lease agreement",
"rent agreement",
"leave and license",
"lease deed",

# payments
"security deposit",
"deposit",
"rent payment",
"arrears",
"rent increase",
"rent revision",

# eviction / possession
"eviction",
"eviction notice",
"recovery of possession",
"possession",
"vacate",
"ejectment",

# rights & duties
"tenant rights",
"landlord rights",
"obligation",
"duty",
"consent",

# courts and authorities
"rent court",
"rent tribunal",
"rent authority",
"appeal",
"order",
"application",

# disputes
"rent dispute",
"default",
"non payment",
"termination",
"lease termination",
"tenancy termination",

# property related
"sublet",
"sub lease",
"sub tenancy",
"property manager",
"rental agent",

# legal framework
"maharashtra rent control act",
"model tenancy act"
]

print("\nKeyword coverage:\n")


for k in keywords:
    count = clauses.str.contains(k, regex=False).sum()
    print(f"{k:30} : {count}")


# clause length analysis
df["length"] = df["answer"].str.split().apply(len)

print("\nClause length statistics:\n")
print(df["length"].describe())


# show random sample
print("\nSample clauses:\n")
print(df["answer"].sample(10))