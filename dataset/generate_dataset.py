"""
================================================================================
  LURA-RENT | Tanisha's Data Pipeline
  Step 1 : Extract clauses from PDF rental agreements
  Step 2 : Auto-label each clause using Gemini 2.0 Flash (Teacher Model)
  Step 3 : Export dataset.json ready for Razeen's Unsloth SFTTrainer
================================================================================

  HOW TO RUN:
  -----------
  1. pip uninstall google-generativeai -y
     pip install google-genai pdfplumber tqdm
  2. Paste your Gemini API key into GEMINI_API_KEY below
     OR set environment variable:
       Windows : set GEMINI_API_KEY=AIza...
       Mac/Linux: export GEMINI_API_KEY=AIza...
  3. Place all rental agreement PDFs inside the ./pdfs/ folder
  4. Run: python generate_dataset.py

  FREE TIER LIMITS (Gemini 2.0 Flash):
  -------------------------------------
  - 1,500 requests/day
  - 15 requests/minute
  - Completely free, no credit card needed

  FEATURES:
  ---------
  - Crash-safe: saves after every clause, resume anytime by re-running
  - Rate limit handling with automatic retries + exponential backoff
  - Deduplication: skips duplicate clauses across PDFs
  - Skips non-clause pages (schedules, witness sections, headers)

================================================================================
"""

import os
import re
import json
import time
import pdfplumber
from google import genai
from google.genai import types
from tqdm import tqdm


# ================================================================================
#  CONFIG — Edit these before running
# ================================================================================

PDF_FOLDER        = "./pdfs"             # Folder containing your rental agreement PDFs
OUTPUT_FILE       = "./dataset.json"     # Final output file for Unsloth SFTTrainer
GEMINI_API_KEY    = NONE                  # Paste your key here: "AIza..."
TEACHER_MODEL = "models/gemini-2.5-flash"  # Current free tier model
API_DELAY_SECONDS = 4.0                  # 4s between calls = safe under 15 req/min limit
MAX_RETRIES       = 3                    # Retries per clause on failure
MIN_CLAUSE_LENGTH = 60                   # Segments shorter than this are skipped as noise


# ================================================================================
#  SYSTEM PROMPT — Maharashtra Law Expert Persona
# ================================================================================

SYSTEM_PROMPT = """You are a senior legal expert specializing in Indian real estate law,
with deep expertise in the Maharashtra Rent Control Act, 1999, the Registration Act, 1908,
and the Transfer of Property Act, 1882. You have 20+ years of experience advising tenants
and landlords in Mumbai and Pune on Leave and License agreements.

Your task is to audit individual clauses extracted from Indian residential and commercial
Leave and License agreements governed by Maharashtra state law.

For each clause, respond using EXACTLY this format with no deviations:

RISK LEVEL: [choose one: Low / Medium / High / Critical]
PLAIN LANGUAGE SUMMARY: [2-3 sentences explaining what this clause means in simple language a first-time tenant in Mumbai can understand. Avoid legal jargon.]
LEGAL ASSESSMENT: [2-3 sentences assessing whether this clause is standard, unusual, one-sided, or potentially unlawful under the Maharashtra Rent Control Act, 1999 or other applicable Indian law. Cite section numbers where relevant.]
TENANT ADVISORY: [2-3 sentences of specific, actionable advice. What should the tenant negotiate, clarify, or watch out for before signing?]

Strict rules:
- Reference only Indian law. Never cite US, UK, or any non-Indian statute.
- Use Rs. or INR for all currency references.
- If a clause is fair and standard, say so. Do not manufacture risk.
- If a clause is missing important protections (e.g., no refund timeline for deposit), flag the omission.
- Keep tone professional but accessible."""


# ================================================================================
#  STEP 1 — Extract raw text from PDFs
# ================================================================================

def extract_text_from_pdf(pdf_path):
    full_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n\n"
    except Exception as e:
        print(f"  [WARNING] Could not read {os.path.basename(pdf_path)}: {e}")
    return full_text


# ================================================================================
#  STEP 2 — Segment text into individual clauses
# ================================================================================

SKIP_PATTERNS = [
    r"^Page \d+ of \d+",
    r"^SCHEDULE [I|II|III|IV|V]+",
    r"^IN WITNESS WHEREOF",
    r"^Sr Number",
    r"^Item\s+No\.",
    r"^\d+\s+(Fan|Tube|Bulb|Bed|Sofa|Table|Chair|Cupboard|Air|Gas|Water|Curtain|Other)",
    r"https?://",
    r"^Stamp Duty",
    r"^Registration Fee",
    r"Licensor\s*$",
    r"Licensee\s*$",
    r"Witness \d",
    r"^\d+/\d+/\d+,",
    r"^Particulars\s+Amount",
    r"^GRN/Transaction",
]

PARTY_DETAIL_SIGNALS = [
    "Age : About", "PAN:", "Aadhaar:", "Residing at:", "Floor No:",
    "Building Name:", "Block Sector:", "Road:", "HEREINAFTER called"
]

def is_noise_line(line):
    line = line.strip()
    if not line:
        return True
    for pattern in SKIP_PATTERNS:
        if re.match(pattern, line, re.IGNORECASE):
            return True
    return False

def segment_clauses(text):
    clause_pattern = re.compile(
        r'(?=(?:^|\n)\s*\d{1,2}[)\.](?!\d)\s)',
        re.MULTILINE
    )
    raw_segments = clause_pattern.split(text)
    cleaned = []
    for seg in raw_segments:
        if any(signal in seg for signal in PARTY_DETAIL_SIGNALS):
            continue
        lines = seg.split('\n')
        good_lines = [l for l in lines if not is_noise_line(l)]
        seg_clean = re.sub(r'\s+', ' ', ' '.join(good_lines)).strip()
        if len(seg_clean) >= MIN_CLAUSE_LENGTH:
            cleaned.append(seg_clean)
    return cleaned

def load_all_clauses(folder):
    pdf_files = [f for f in os.listdir(folder) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print(f"\n[ERROR] No PDF files found in '{folder}'.")
        print("  Add your rental agreement PDFs there and re-run.")
        return []

    print(f"\n[Step 1] Found {len(pdf_files)} PDF(s) in '{folder}'")
    all_clauses = []

    for filename in pdf_files:
        path = os.path.join(folder, filename)
        print(f"  -> Reading: {filename}")
        text = extract_text_from_pdf(path)
        if not text.strip():
            print(f"     [SKIP] No readable text found.")
            continue
        clauses = segment_clauses(text)
        print(f"     Extracted {len(clauses)} clause segments.")
        all_clauses.extend(clauses)

    seen = set()
    unique = []
    for c in all_clauses:
        key = re.sub(r'\s+', ' ', c.lower().strip())
        if key not in seen:
            seen.add(key)
            unique.append(c)

    removed = len(all_clauses) - len(unique)
    print(f"\n[Step 2] Unique clauses after deduplication: {len(unique)} ({removed} duplicates removed)")
    return unique


# ================================================================================
#  STEP 3 — Resume support
# ================================================================================

def load_existing(output_file):
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
            done = {e["clause"] for e in existing}
            print(f"\n[Resume] {len(existing)} entries already in dataset.json - skipping these.")
            return existing, done
        except (json.JSONDecodeError, KeyError):
            print("\n[Resume] dataset.json exists but is malformed - starting fresh.")
    return [], set()


# ================================================================================
#  STEP 4 — Call Gemini 2.0 Flash
# ================================================================================

def get_analysis(client, clause):
    prompt = (
        "Please audit the following clause from an Indian Leave and License "
        "rental agreement (Maharashtra):\n\n"
        f"---\n{clause}\n---\n\n"
        "Provide your structured legal audit in the exact format specified."
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=TEACHER_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.2,
                    max_output_tokens=700,
                )
            )
            return response.text.strip()
        except Exception as e:
            print(f"\n    [Attempt {attempt}/{MAX_RETRIES}] Error: {type(e).__name__}: {e}")
            if attempt < MAX_RETRIES:
                wait = API_DELAY_SECONDS * (2 ** attempt)
                print(f"    Retrying in {wait:.1f}s...")
                time.sleep(wait)
            else:
                print(f"    [FAILED] Skipping clause after {MAX_RETRIES} attempts.")
                return None


# ================================================================================
#  STEP 5 — Save (crash-safe)
# ================================================================================

def save(dataset, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)


# ================================================================================
#  MAIN
# ================================================================================

def main():
    print("=" * 65)
    print("  LURA-RENT | Dataset Generation Pipeline")
    print("  Teacher Model : Gemini 2.0 Flash (Free Tier)")
    print("  Output        : dataset.json (Unsloth SFTTrainer ready)")
    print("=" * 65)

    # Resolve API key
    api_key = GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("\n[ERROR] Gemini API key not found.")
        print("  Paste your key into GEMINI_API_KEY at the top of this script.")
        print("  Or set: set GEMINI_API_KEY=AIza...  (Windows)")
        return

    # Init Gemini client (new google-genai SDK)
    client = genai.Client(api_key=api_key)
    print(f"\n[OK] Gemini client ready. Model: {TEACHER_MODEL}")

    # Setup PDF folder
    if not os.path.exists(PDF_FOLDER):
        os.makedirs(PDF_FOLDER)
        print(f"\n[INFO] Created '{PDF_FOLDER}/' folder.")
        print("  Add your rental agreement PDFs there and re-run.")
        return

    # Step 1+2: Extract
    all_clauses = load_all_clauses(PDF_FOLDER)
    if not all_clauses:
        return

    # Step 3: Resume
    dataset, already_done = load_existing(OUTPUT_FILE)
    pending = [c for c in all_clauses if c not in already_done]

    print(f"\n[Info] Clauses pending analysis : {len(pending)}")
    print(f"[Info] Estimated time           : ~{len(pending) * API_DELAY_SECONDS / 60:.1f} minutes")
    print(f"[Info] Cost                     : FREE (Gemini free tier)\n")

    if not pending:
        print("[DONE] All clauses already processed! dataset.json is complete.")
        return

    # Step 4+5: Label and save
    print("[Step 3] Sending clauses to Gemini 2.0 Flash...\n")
    failed = 0

    for clause in tqdm(pending, desc="Labelling clauses", unit="clause"):
        analysis = get_analysis(client, clause)
        if analysis:
            dataset.append({"clause": clause, "analysis": analysis})
            save(dataset, OUTPUT_FILE)
        else:
            failed += 1
        time.sleep(API_DELAY_SECONDS)

    print("\n" + "=" * 65)
    print("  COMPLETE!")
    print(f"  Total entries in dataset.json : {len(dataset)}")
    print(f"  Newly labelled this run       : {len(pending) - failed}")
    print(f"  Failed / skipped              : {failed}")
    print(f"  Output path                   : {os.path.abspath(OUTPUT_FILE)}")
    print("=" * 65)
    print("\n  dataset.json is ready for Razeen's Unsloth SFTTrainer")
    print("  Hand this file + the pdfs/ folder to Tanisha.\n")


if __name__ == "__main__":
    main()