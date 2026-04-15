# GURPREET_SETUP.md
## Lura-Rent — Frontend Setup & Handoff Guide
**For:** Gurpreet Singh Sandhu (Roll No. 2403143)  
**Branch:** `dev-ui`  
**Last updated by:** Razeen Husain Saiyed

---

## What You Need to Do

Your job is to get the Streamlit app running on your laptop and connect it to Razeen's model. Everything else is already done — the model is trained, the UI code is written, and this guide tells you exactly what to run.

---

## Step 1 — Get the Model Files from Razeen

Razeen will share two files with you via Google Drive:

| File | Size | What it is |
|---|---|---|
| `llama-3.2-3b-instruct.Q4_K_M.gguf` | ~1.9 GB | The trained model |
| `Modelfile` | tiny | Ollama configuration |

Save both files in the same folder, for example:
```
C:\Gurpreet\LuraRent\
```

---

## Step 2 — Install Ollama

1. Download Ollama from [https://ollama.com](https://ollama.com)
2. Run the installer
3. Verify it installed correctly by opening PowerShell and running:
```powershell
ollama --version
```

---

## Step 3 — Load the Model into Ollama

Open PowerShell, navigate to the folder where you saved the files, and run:

```powershell
cd "C:\Gurpreet\LuraRent"
ollama create lura-rent -f Modelfile
```

Wait for it to finish. Then verify the model loaded:
```powershell
ollama list
```

You should see `lura-rent:latest` in the list.

**Keep Ollama running in the background whenever you use the app.** It runs as a background service automatically after installation — you do not need to start it manually.

---

## Step 4 — Set Up the Python Environment

Open PowerShell and run:

```powershell
pip install streamlit PyPDF2 ollama
```

---

## Step 5 — Get the App Code

Pull the latest code from the `dev-ui` branch:

```powershell
git checkout dev-ui
git pull origin dev-ui
```

Make sure you have these files in your project folder:

```
app.py
.streamlit/
    config.toml
```

---

## Step 6 — Run the App

```powershell
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

---

## How the App Works (Read This Before Testing)

The app has **three features** after a PDF is analysed:

### Feature 1 — AI Audit (already existed)
- User uploads a PDF
- Clicks **🚀 Run AI Audit**
- Model returns: Overall Summary, The Good, The Bad, Gray Areas, Detailed Clause Analysis

### Feature 2 — Advice on Next Steps (NEW)
- After the audit completes, a red **⚡ Advice on Next Steps** button appears
- Clicking it sends the audit report back to the model with a second prompt
- Model returns: specific legal remedies for each High/Critical clause, citing exact sections of the Maharashtra Rent Control Act, 1999
- This is a **separate second call** — it only fires when the button is clicked

### Feature 3 — Ask Questions (already existed)
- Green **💬 Ask Questions** button opens a chat window
- User can ask follow-up questions about the contract

### Export
- Blue **📥 Export Full Report** button downloads the audit + advice as a `.txt` file
- If advice has been generated, it is included in the export automatically

---

## What Changed in This Version of app.py

If you had an older version of `app.py`, here is exactly what changed:

| # | Change | Why |
|---|---|---|
| 1 | `MODEL_NAME = "lura-rent"` | Fixed — old code used `lura-rent-model` which does not match the actual Ollama model name |
| 2 | `get_advice()` function added | New — second prompt call for legal remedies |
| 3 | `advice_window()` dialog added | New — displays the Next Steps output |
| 4 | Three-column button layout | New — replaces the single chat button |
| 5 | `uploaded_filename` session state | Fixed — prevents stale text when a second PDF is uploaded |
| 6 | Reset button in sidebar | New — cleanly resets all state for a new document |
| 7 | Export includes advice if generated | Improved — full report in one file |

---

## Troubleshooting

### "Failed to connect to model" error
- Ollama is not running. Open PowerShell and run: `ollama serve`
- Or restart your computer — Ollama should start automatically

### "model not found" error  
- The model name in Ollama does not match. Run `ollama list` and confirm you see `lura-rent:latest`
- If not, re-run: `ollama create lura-rent -f Modelfile`

### App gives a one-line response
- This was the old model. Razeen has retrained — make sure you have the new `.gguf` file from him

### PDF uploads but shows blank extracted text
- The PDF is a scanned image, not a native text PDF. The app only works with native (text-selectable) PDFs. OCR is not supported.

### Second upload does not clear old results
- Make sure you are using the latest `app.py` from this branch. The fix for this is included.

---

## Testing Checklist

Before the final presentation, verify each of these:

- [ ] `ollama list` shows `lura-rent:latest`
- [ ] App opens at `http://localhost:8501`
- [ ] Upload one of the sample PDFs from the `/pdfs` folder
- [ ] **Run AI Audit** produces a full response with all sections (not one line)
- [ ] **Advice on Next Steps** button appears after audit completes
- [ ] Clicking it produces legal remedies with section numbers
- [ ] **Ask Questions** button opens the chat window
- [ ] Chat follow-up question gets a response
- [ ] **Export Full Report** downloads a `.txt` file
- [ ] Uploading a second PDF clears the old results

---

## Contact

If something is broken and you cannot fix it:
- WhatsApp Razeen — he handles the model side
- The `get_advice()` function and model name are the two most likely failure points