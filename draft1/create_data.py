import pandas as pd 
import re
import os
import pdfplumber

pdf_files = [
    "Model-Tenancy-Act-English-02_06_2021.pdf",
    "eng_maharashtra_rent_control_ac.pdf",
]

def extract_simple(filename):
    clauses = []
    with pdfplumber.open(filename) as pdf:
        for page_num, page in enumerate(pdf.pages[5:], 6):  # SKIP FIRST 5 PAGES
            text = page.extract_text()
            if not text:
                continue
                
            text = re.sub(r'\n+', ' ', text)
            
            # SIMPLIFIED: Just grab paragraphs with tenancy keywords
            paras = re.split(r'\.\s*(?=[A-Z][a-z]', text)  # Split on sentences
            for para in paras:
                para = para.strip()
                if (len(para) > 50 and 
                    any(word in para.lower() for word in ['tenant', 'landlord', 'rent', 'premises', 'eviction']) and
                    not any(word in para.upper() for word in ['SCHEDULE', 'Wada', 'Village', 'Taluka'])):
                    clauses.append({
                        'clause': para[:600],
                        'page': page_num,
                        'source_pdf': filename
                    })
    return clauses

# RUN
all_clauses = []
for pdf in pdf_files:
    extracted = extract_simple(pdf)
    print(f"{pdf} → {len(extracted)} clauses")
    all_clauses.extend(extracted)

df = pd.DataFrame(all_clauses).drop_duplicates('clause')
df.to_csv('tenancy_raw.csv', index=False)
print(f"\nFINAL: {len(df)} clauses")
print("\nSAMPLES:")
for i, c in enumerate(df['clause'].head(3)):
    print(f"{i+1}. {c[:200]}...")
