# Lura-Rent | Data Pipeline
### Tanisha's Part — Data Lead

---

## What This Does

This folder contains the **dataset generation pipeline** for Lura-Rent.

It takes real Indian rental agreement PDFs, extracts individual legal clauses from them, and uses **Gemini 2.5 Flash** (Google's free AI API) to automatically generate a legal expert analysis for each clause.

The final output is `dataset.json` — the training dataset that Razeen feeds into the **Unsloth SFTTrainer** to fine-tune the Llama-3.2-3B model.

---

## How It Fits Into the Project

```
[ Tanisha — Data Pipeline ]         ← YOU ARE HERE
  PDFs → extract clauses
  clauses → Gemini analysis
  output → dataset.json
         ↓
[ Razeen — AI Fine-Tuning ]
  dataset.json → Unsloth SFTTrainer
  fine-tuned model → Ollama (.gguf)
         ↓
[ Gurpreet — Frontend ]
  Streamlit UI → Ollama API
```

---

## Output Format

Each entry in `dataset.json` looks like this:

```json
{
  "clause": "Raw legal clause text extracted from the PDF",
  "analysis": "RISK LEVEL: High\nPLAIN LANGUAGE SUMMARY: ...\nLEGAL ASSESSMENT: ...\nTENANT ADVISORY: ..."
}
```

This is the exact format Razeen's Unsloth `SFTTrainer` expects. Do not change the structure.

---

## Folder Structure

```
dataset/
  ├── generate_dataset.py   # Main pipeline script — this is what you run
  ├── requirements.txt      # Python dependencies
  ├── README.md             # This file
  ├── pdfs/                 # Drop your rental agreement PDFs here
  │     ├── Sample-Agreement.pdf
  │     ├── residential_sample_draft_leave_and_license.pdf
  │     └── leave-and-license-agreement-format.pdf
  └── .gitignore            # Keeps generated files out of Git
```

> ⚠️ `dataset.json` and the contents of `pdfs/` are NOT committed to Git.
> Generate `dataset.json` locally by running the script.

---

## Setup — Do This Once

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Get a Gemini API Key (free)

1. Go to [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click **Create API Key**
4. Copy the key (starts with `AIza...`)

### 3. Add your API key to the script

Open `generate_dataset.py` and find this line near the top:

```python
GEMINI_API_KEY = None
```

Replace it with your key:

```python
GEMINI_API_KEY = "AIza..."
```

> 💡 Never commit your API key to GitHub. Keep it only in your local copy of the script.

---

## Running the Pipeline

### Step 1 — Add PDFs

Place your rental agreement PDFs inside the `./pdfs/` folder.
Any Maharashtra Leave and License agreement PDF works.
The more PDFs you add, the larger and better the dataset.

### Step 2 — Run the script

```bash
python generate_dataset.py
```

### Step 3 — Wait

The script will:
1. Read all PDFs and extract legal clauses
2. Deduplicate clauses across PDFs
3. Send each clause to Gemini for legal analysis
4. Save results to `dataset.json` after every clause (crash-safe)

Expected time: ~2 minutes for 32 clauses (free tier).

### Step 4 — Hand dataset.json to Razeen

Send him the generated `dataset.json` file directly (WhatsApp, Drive, etc.)
Do not push it to GitHub.

---

## Resume After Interruption

If the script crashes or you stop it, just run it again:

```bash
python generate_dataset.py
```

It automatically reads the existing `dataset.json` and skips already-processed clauses.
It will only process the ones that are missing.

---

## Adding More PDFs Later

Data sourcing is an ongoing job. Whenever you find new Maharashtra rental agreement PDFs:

1. Drop them into the `./pdfs/` folder
2. Run `python generate_dataset.py` again
3. The script will only process the new clauses — existing ones are skipped

Good sources for PDFs:
- [leavelicense.com](http://www.leavelicense.com/downloads/Sample-Agreement.pdf)
- [IGR Maharashtra Portal](https://efilingigr.maharashtra.gov.in) — registered agreements
- NoBroker, IndiaFilings, Vakil Search — sample templates

---

## Free Tier Limits (Gemini 2.5 Flash)

| Limit | Value |
|---|---|
| Requests per day | 1,500 |
| Requests per minute | 15 |
| Cost | Free |

The script automatically waits 4 seconds between requests to stay within the per-minute limit.

---

## Troubleshooting

| Error | Fix |
|---|---|
| `404 NOT_FOUND` for model | Change `TEACHER_MODEL` to `"models/gemini-2.5-flash"` in the script |
| `429 RESOURCE_EXHAUSTED` | You've hit the rate limit — wait a minute and re-run |
| `No PDF files found` | Make sure your PDFs are inside the `./pdfs/` folder |
| PDF reads as empty | The PDF may be scanned/image-based — pdfplumber can only read text-based PDFs |
| Clauses look like noise | The PDF structure is unusual — tell Razeen and he can adjust the segmentation logic |

---

## Contact

- **Razeen** — AI Lead — built this pipeline, handles model fine-tuning
- **Gurpreet** — Frontend Lead — Streamlit UI

*Lura-Rent | TSEC Mumbai | B.E. Computer Engineering | AY 2025-26*