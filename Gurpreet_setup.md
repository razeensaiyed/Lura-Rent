# Lura-Rent — Frontend Setup Guide for Gurpreet
**Prepared by:** Razeen (AI Lead)  
**Branch:** `dev-model/razeen`  
**Last updated:** April 2026

---

## What this file is

This is everything you need to get the Lura-Rent AI model running locally on your machine so you can connect your Streamlit app to it.

---

## ⚠️ Important — Read This First

The `.gguf` model file I am giving you right now is a **temporary/early version** of the fine-tuned model. Training is still in progress. Once I am done with the full training run, I will give you a new `.gguf` file to replace it with. Your Streamlit code will **not need any changes** — you just replace the file and re-run one command.

---

## What Razeen will give you (outside GitHub — via Google Drive or USB)

| File | Size | What it is |
|---|---|---|
| `llama-3.2-3b-instruct.Q4_K_M.gguf` | ~1.9 GB | The fine-tuned Lura-Rent AI model |
| `Modelfile` | Tiny | Ollama configuration file |

> **Why not on GitHub?** GitHub has a 100MB file limit. The model is 1.9GB. Share via Google Drive or USB only.

---

## Step 1 — Install Ollama

Download and install Ollama from: **https://ollama.com**

It is a one-click installer. Available for Windows, Mac, and Linux.

Verify it installed correctly by opening a terminal and running:

```bash
ollama --version
```

You should see something like `ollama version is 0.x.x`.

---

## Step 2 — Put both files in the same folder

Create a folder anywhere on your machine, for example:
```
C:\Lura-Rent\model\
```

Place both files in it:
```
C:\Lura-Rent\model\llama-3.2-3b-instruct.Q4_K_M.gguf
C:\Lura-Rent\model\Modelfile
```

> **Critical:** Both files must be in the same folder. The Modelfile references the `.gguf` by relative path.

---

## Step 3 — Register the model with Ollama

Open a terminal, navigate to the folder, and run:

```bash
cd "C:\Lura-Rent\model"
ollama create lura-rent -f Modelfile
```

You should see:
```
transferring model data
creating model layer
success
```

The model is now registered under the name `lura-rent`.

---

## Step 4 — Make sure Ollama is running when you use the app

Before launching your Streamlit app, run:

```bash
ollama serve
```

Keep this terminal open. Ollama must be running in the background for the API calls to work.

> On Windows, Ollama may already be running in the system tray after installation. If `ollama serve` says "address already in use", that means it is already running — you are good to go.

---

## Step 5 — How to call the model from your Streamlit app

The Ollama API runs locally at:
```
http://localhost:11434/api/generate
```

Here is the exact Python code for the API call:

```python
import requests

def analyze_clause(clause: str) -> str:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "lura-rent",
            "prompt": f"Analyze this clause: {clause}",
            "stream": False
        }
    )
    return response.json()["response"]
```

Call it like this:
```python
clause = "The landlord may terminate this agreement at any time without notice."
analysis = analyze_clause(clause)
print(analysis)
```

The model will return a response starting with `RISK LEVEL:` followed by a full legal analysis.

---

## Step 6 — Replacing the model (when Razeen gives you the updated .gguf)

When I finish the full training run, I will give you a new `.gguf` file.

To update:
1. Replace the old `.gguf` file in your folder with the new one
2. Re-run this command:
```bash
cd "C:\Lura-Rent\model"
ollama create lura-rent -f Modelfile
```

That's it. Your Streamlit code stays exactly the same.

---

## Quick Reference — Expected model output format

The model returns analysis in this structure:

```
RISK LEVEL: Critical / High / Medium / Low
PLAIN LANGUAGE SUMMARY: ...
LEGAL ASSESSMENT: ...
TENANT ADVISORY: ...
```

You can parse this in your UI to colour-code by risk level if you want.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `connection refused` on API call | Run `ollama serve` first |
| `model not found` | Re-run `ollama create lura-rent -f Modelfile` |
| `file not found` during create | Make sure both files are in the same folder |
| Slow first response | Normal — model loads into memory on first call (~10–15 sec) |

---

## Contact

Any issues → message Razeen directly.