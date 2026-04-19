"""
================================================================================
  LURA-RENT | Dataset Repair Script
  Tanisha's Data Pipeline — Repair Mode

  What this script does:
  ----------------------
  1. Loads the existing dataset.json (114 entries)
  2. Detects truncated entries (missing TENANT ADVISORY or cut-off mid-sentence)
  3. Re-sends ONLY those broken clauses to Gemini for a fresh, complete analysis
  4. Saves the fully repaired dataset as dataset_fixed.json
  5. NEVER overwrites your original dataset.json

  Root cause of truncation:
  -------------------------
  The original script used max_output_tokens=700, which was too low for
  complete 4-section responses. This script uses 1024 tokens.

  HOW TO RUN:
  -----------
  1. pip install google-genai tqdm
  2. Paste your Gemini API key into GEMINI_API_KEY below
  3. Place this script in the same folder as dataset.json
  4. Run: python fix_dataset.py
  5. When done, rename dataset_fixed.json → dataset.json before retraining

  FREE TIER LIMITS (Gemini 2.5 Flash):
  -------------------------------------
  - 1,500 requests/day
  - 15 requests/minute
  - 78 broken entries → ~6 minutes to repair

================================================================================
"""

import os
import re
import json
import time
from google import genai
from google.genai import types
from tqdm import tqdm


# ================================================================================
#  CONFIG — Edit these before running
# ================================================================================

INPUT_FILE        = "./dataset.json"          # Your existing broken dataset
OUTPUT_FILE       = "./dataset_fixed.json"    # Repaired output — never touches original
GEMINI_API_KEY    = "AIzaSyCGBN7_oX6r1gSnyw58XsVOktHMqjGYxOU"                        # Paste your Gemini API key here: "AIza..."
TEACHER_MODEL     = "models/gemini-2.5-flash"
API_DELAY_SECONDS = 4.0                       # Safe under 15 req/min free tier limit
MAX_RETRIES       = 3


# ================================================================================
#  SYSTEM PROMPT — Same as original pipeline for consistency
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
- You MUST complete all four sections. Never stop mid-sentence.
- Reference only Indian law. Never cite US, UK, or any non-Indian statute.
- Use Rs. or INR for all currency references.
- If a clause is fair and standard, say so. Do not manufacture risk.
- If a clause is missing important protections (e.g., no refund timeline for deposit), flag the omission.
- Keep tone professional but accessible."""


# ================================================================================
#  TRUNCATION DETECTION
# ================================================================================

def is_truncated(analysis: str) -> bool:
    """
    Returns True if the analysis is incomplete.
    Two signals:
      1. Missing TENANT ADVISORY section entirely
      2. Last character is not a sentence-ending punctuation mark
    """
    if not analysis or not analysis.strip():
        return True

    has_tenant_advisory = "TENANT ADVISORY" in analysis
    last_char = analysis.strip()[-1]
    ends_properly = last_char in [".", "!", "?", '"', "'"]

    return not has_tenant_advisory or not ends_properly


# ================================================================================
#  CALL GEMINI
# ================================================================================

def get_analysis(client, clause: str) -> str | None:
    prompt = (
        "Please audit the following clause from an Indian Leave and License "
        "rental agreement (Maharashtra):\n\n"
        f"---\n{clause}\n---\n\n"
        "Provide your structured legal audit in the exact format specified. "
        "You MUST complete all four sections: RISK LEVEL, PLAIN LANGUAGE SUMMARY, "
        "LEGAL ASSESSMENT, and TENANT ADVISORY. Do not stop mid-sentence."
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=TEACHER_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.2,
                    max_output_tokens=1024,   # Fixed: was 700 in original, caused truncation
                )
            )
            result = response.text.strip()

            # Verify the response itself is not truncated before returning
            if is_truncated(result):
                print(f"\n    [WARNING] Gemini returned a truncated response on attempt {attempt}. Retrying...")
                if attempt < MAX_RETRIES:
                    time.sleep(API_DELAY_SECONDS * attempt)
                    continue
                else:
                    print(f"    [FAILED] Still truncated after {MAX_RETRIES} attempts. Skipping.")
                    return None

            return result

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
#  SAVE (crash-safe)
# ================================================================================

def save(dataset: list, output_file: str):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)


# ================================================================================
#  MAIN
# ================================================================================

def main():
    print("=" * 65)
    print("  LURA-RENT | Dataset Repair Script")
    print("  Mode    : Repair truncated entries only")
    print("  Input   : dataset.json")
    print("  Output  : dataset_fixed.json  (original is never touched)")
    print("=" * 65)

    # --- Validate API key ---
    api_key = GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("\n[ERROR] Gemini API key not found.")
        print("  Paste your key into GEMINI_API_KEY at the top of this script.")
        print("  Or run:  set GEMINI_API_KEY=AIza...  (Windows)")
        return

    # --- Load existing dataset ---
    if not os.path.exists(INPUT_FILE):
        print(f"\n[ERROR] {INPUT_FILE} not found.")
        print("  Make sure this script is in the same folder as dataset.json")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    print(f"\n[OK] Loaded {len(dataset)} entries from dataset.json")

    # --- Detect truncated entries ---
    truncated_indices = []
    for i, entry in enumerate(dataset):
        if is_truncated(entry.get("analysis", "")):
            truncated_indices.append(i)

    complete_count = len(dataset) - len(truncated_indices)
    print(f"[OK] Complete entries : {complete_count}")
    print(f"[OK] Truncated entries: {len(truncated_indices)}  ← these will be repaired")
    print(f"[OK] Estimated time   : ~{len(truncated_indices) * API_DELAY_SECONDS / 60:.1f} minutes")
    print(f"[OK] Cost             : FREE (Gemini free tier)\n")

    if not truncated_indices:
        print("[DONE] No truncated entries found. dataset.json is already complete.")
        print("       Saving a clean copy as dataset_fixed.json anyway.")
        save(dataset, OUTPUT_FILE)
        return

    # --- Init Gemini client ---
    client = genai.Client(api_key=api_key)
    print(f"[OK] Gemini client ready. Model: {TEACHER_MODEL}\n")

    # --- Repair loop ---
    print("[Step 1] Repairing truncated entries...\n")
    repaired = 0
    failed = 0

    for idx in tqdm(truncated_indices, desc="Repairing entries", unit="entry"):
        clause = dataset[idx]["clause"]
        old_analysis = dataset[idx]["analysis"]

        new_analysis = get_analysis(client, clause)

        if new_analysis:
            dataset[idx]["analysis"] = new_analysis
            repaired += 1
            # Save after every repair — crash-safe
            save(dataset, OUTPUT_FILE)
        else:
            # Keep the old (broken) analysis rather than losing the entry entirely
            failed += 1
            print(f"\n  [KEPT ORIGINAL] Entry {idx + 1} could not be repaired — keeping old analysis.")

        time.sleep(API_DELAY_SECONDS)

    # --- Final report ---
    print("\n" + "=" * 65)
    print("  REPAIR COMPLETE!")
    print(f"  Total entries        : {len(dataset)}")
    print(f"  Successfully repaired: {repaired}")
    print(f"  Could not repair     : {failed}  (original text kept)")
    print(f"  Output saved to      : {os.path.abspath(OUTPUT_FILE)}")
    print("=" * 65)
    print()
    print("  NEXT STEPS:")
    print("  1. Review dataset_fixed.json to spot-check a few entries")
    print("  2. If satisfied, rename it to dataset.json")
    print("  3. Hand to Razeen for retraining on Colab")
    print()


if __name__ == "__main__":
    main()