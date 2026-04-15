import streamlit as st
import PyPDF2
import ollama

# ── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Lura-Rent | AI Auditor",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    @keyframes slideUpFade {
        0% { opacity: 0; transform: translateY(20px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    .block-container { animation: slideUpFade 0.6s ease-out forwards; padding-top: 2rem !important; }
    [data-testid="stSidebar"]::before { content: ''; display: block; height: 4px; width: 100%; background: linear-gradient(90deg, #10B981, #047857); }
    [data-testid="column"] { background: #FFFFFF; padding: 1.5rem; border-radius: 4px; box-shadow: 0 4px 6px -1px rgba(15,23,42,0.05); border: 1px solid #E2E8F0; }

    .stButton > button {
        border-radius: 4px; font-weight: 600;
        background-color: #059669 !important; color: #FFFFFF !important;
        border: none; transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px -1px rgba(5,150,105,0.2);
    }
    .stButton > button:hover {
        background-color: #047857 !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 12px -1px rgba(5,150,105,0.3);
    }

    div[data-testid="stButton"]:has(button[kind="primary"]) > button,
    .cta-row .stButton > button {
        font-size: 1.05rem !important;
        padding: 0.85rem 2rem !important;
        border-radius: 10px !important;
        background: linear-gradient(135deg, #059669, #047857) !important;
        box-shadow: 0 6px 20px rgba(5,150,105,0.4) !important;
        letter-spacing: 0.01em !important;
    }

    [data-testid="stFileUploadDropzone"] { border-radius: 4px; border: 2px dashed #A7F3D0 !important; background-color: #F8FAFC !important; }
    [data-testid="stFileUploadDropzone"]:hover { background-color: #ECFDF5 !important; border-color: #10B981 !important; }

    [data-testid="stDialog"] > div { border-radius: 16px !important; overflow: hidden !important; box-shadow: 0 25px 60px rgba(0,0,0,0.18) !important; }

    [data-testid="stChatMessage"] { border-radius: 12px !important; padding: 0.75rem 1rem !important; margin-bottom: 0.5rem !important; border: none !important; box-shadow: none !important; }
    div[class*="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) { background: linear-gradient(135deg, #059669, #047857) !important; color: white !important; margin-left: 10% !important; }
    div[class*="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) { background: #F1F5F9 !important; margin-right: 10% !important; line-height: 1.6 !important;}
    [data-testid="chatAvatarIcon"] { border-radius: 8px !important; }

    [data-testid="stChatInput"] { border-radius: 12px !important; border: 2px solid #E2E8F0 !important; }
    [data-testid="stChatInput"]:focus-within { border-color: #10B981 !important; box-shadow: 0 0 0 3px rgba(16,185,129,0.1) !important; }
    </style>
""", unsafe_allow_html=True)


# ── Constants ─────────────────────────────────────────────────────────────────
MODEL_NAME = "lura-rent"   # FIX: was 'lura-rent-model' — must match `ollama list`


# ── Logic Layer ───────────────────────────────────────────────────────────────
def extract_text_from_pdf(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None


def get_advice(audit_report: str) -> str:
    """
    Second prompt call — fires only when user clicks 'Advice on Next Steps'.
    Takes the full audit report and extracts actionable legal remedies,
    scaled by risk level, citing exact Maharashtra Rent Control Act sections.
    """

    # Hardcoded Act reference — injected as context so the model cites correctly
    act_reference = """
KEY SECTIONS — Maharashtra Rent Control Act, 1999:
- Section 8  : Court may fix standard rent on application by tenant
- Section 10 : Charging excess rent → imprisonment up to 3 months or fine up to Rs.5,000 or both
- Section 14 : Landlord must keep premises in repair; tenant may repair after 15-day notice and deduct cost from rent
- Section 15 : Landlord cannot file eviction suit for non-payment until 90 days after written demand notice; tenant can deposit arrears in court to avoid eviction
- Section 16 : Exhaustive list of valid eviction grounds (damage, nuisance, subletting, bona fide need, non-user for 6 months, etc.)
- Section 24 : Leave & License expiry — landlord must apply to competent authority for eviction order, not self-evict
- Section 28 : Landlord may inspect only at reasonable time with prior notice
- Section 29 : Landlord cannot cut off essential services (water, electricity, lift, sanitation); fine Rs.100/day; imprisonment up to 3 months for continued default
- Section 31 : Landlord must issue rent receipt; fine Rs.100/day for failure
- Section 33 : Jurisdiction — Court of Small Causes (Brihan Mumbai); Civil Judge Junior Division (other Maharashtra areas)
- Section 55 : Agreement must be in writing and registered by Licensor; failure = imprisonment up to 3 months or fine up to Rs.5,000
"""

    advice_prompt = f"""You are Lura-Rent, a legal AI assistant specializing in the Maharashtra Rent Control Act, 1999.

The following is a completed audit report of a rental agreement:

{audit_report}

{act_reference}

Your task: For each HIGH or CRITICAL risk clause identified in the audit above, provide specific next steps the tenant should take.

STRICT RULES:
1. Start immediately with the advice. No filler like "Here are the next steps".
2. Scale depth to risk level:
   - LOW risk: One sentence — "This is standard, no action needed."
   - MEDIUM risk: 2-3 sentences — suggest what to negotiate before signing.
   - HIGH risk: Paragraph — quote the relevant Act section, explain the tenant's rights, suggest what to demand in writing.
   - CRITICAL risk: Full guidance — exact section of the Act, penalty the landlord faces, which court to approach, what to file.
3. Use this exact format for each clause:

### ⚡ NEXT STEPS: [paste the clause risk level and first 8 words of the clause]

**What You Can Do:**
[Specific actionable steps]

**Relevant Law:**
[Exact section of Maharashtra Rent Control Act, 1999 that applies]

**Recommended Action:**
[What to do right now — negotiate, demand in writing, approach court, file complaint]

---

Only cover HIGH and CRITICAL clauses. Skip LOW and MEDIUM unless there is a specific action the tenant must take before signing."""

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are Lura-Rent, a legal AI assistant for the Maharashtra Rent Control Act, 1999. You give specific, actionable legal advice to tenants. Never use filler phrases. Always cite exact section numbers."},
            {"role": "user", "content": advice_prompt}
        ],
        stream=False
    )
    return response['message']['content']


# ── Session State ─────────────────────────────────────────────────────────────
for key, default in {
    "extracted_text": "",
    "uploaded_filename": "",       # NEW: tracks filename to detect new uploads
    "audit_report": "",
    "advice_report": "",           # NEW: stores the Next Steps output separately
    "chat_history": [],
    "display_chat": [],
    "is_generating": False,
    "is_getting_advice": False,    # NEW: spinner state for advice call
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ── Chat Dialog ───────────────────────────────────────────────────────────────
@st.dialog("💬 Ask Lura-Rent Anything", width="large")
def chat_window():
    st.markdown("""
        <div style="background:linear-gradient(135deg,#059669,#047857);border-radius:12px;padding:1.2rem 1.5rem;margin-bottom:1rem;">
            <div style="display:flex;align-items:center;gap:0.75rem;">
                <div style="background:rgba(255,255,255,0.2);border-radius:8px;padding:0.5rem;font-size:1.4rem;">⚖️</div>
                <div>
                    <div style="color:white;font-weight:700;font-size:1.05rem;">Lura-Rent Legal Assistant</div>
                    <div style="color:#A7F3D0;font-size:0.78rem;">Powered by local AI · Maharashtra Rent Control Act</div>
                </div>
                <div style="margin-left:auto;background:rgba(255,255,255,0.15);border-radius:20px;padding:0.25rem 0.75rem;color:white;font-size:0.75rem;">🟢 Online</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    with st.expander("📋 View Initial Audit Summary", expanded=False):
        st.markdown(st.session_state["audit_report"])

    if not st.session_state["display_chat"]:
        st.markdown("**💡 Suggested Questions**")
        suggestions = [
            "Is the security deposit amount legal under Maharashtra law?",
            "Can the landlord evict me without prior notice?",
            "Are the maintenance responsibilities fairly divided?",
            "What are my rights if the landlord raises rent suddenly?",
        ]
        c1, c2 = st.columns(2)
        for i, q in enumerate(suggestions):
            with (c1 if i % 2 == 0 else c2):
                if st.button(q, key=f"sugg_{i}", use_container_width=True):
                    st.session_state["display_chat"].append({"role": "user", "content": q})
                    st.session_state["chat_history"].append({"role": "user", "content": q})
                    st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)

    st.divider()

    chat_container = st.container(height=400)
    with chat_container:
        if not st.session_state["display_chat"]:
            st.markdown(
                '<div style="text-align:center;color:#94A3B8;padding:3rem 1rem;font-size:0.9rem;">'
                'Ask me anything about your rental agreement ↓</div>',
                unsafe_allow_html=True
            )
        for msg in st.session_state["display_chat"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if prompt := st.chat_input("e.g. Is clause 4 enforceable under Maharashtra law?"):
        st.session_state["display_chat"].append({"role": "user", "content": prompt})
        st.session_state["chat_history"].append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                try:
                    with st.spinner("Thinking..."):
                        response = ollama.chat(
                            model=MODEL_NAME,
                            messages=st.session_state["chat_history"],
                            stream=False
                        )
                        reply_text = response['message']['content']
                    st.markdown(reply_text)
                    st.session_state["display_chat"].append({"role": "assistant", "content": reply_text})
                    st.session_state["chat_history"].append({"role": "assistant", "content": reply_text})
                except Exception as e:
                    st.error(f"Model Error: {str(e)}")


# ── Next Steps Dialog ─────────────────────────────────────────────────────────
@st.dialog("⚡ Advice on Next Steps", width="large")
def advice_window():
    st.markdown("""
        <div style="background:linear-gradient(135deg,#DC2626,#991B1B);border-radius:12px;padding:1.2rem 1.5rem;margin-bottom:1rem;">
            <div style="display:flex;align-items:center;gap:0.75rem;">
                <div style="background:rgba(255,255,255,0.2);border-radius:8px;padding:0.5rem;font-size:1.4rem;">⚡</div>
                <div>
                    <div style="color:white;font-weight:700;font-size:1.05rem;">Legal Remedies & Next Steps</div>
                    <div style="color:#FCA5A5;font-size:0.78rem;">Powered by local AI · Maharashtra Rent Control Act, 1999</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # If advice already generated, just show it
    if st.session_state["advice_report"]:
        st.markdown(st.session_state["advice_report"])
        return

    # Otherwise generate it now
    with st.spinner("⏳ Generating legal remedies based on identified risks..."):
        try:
            advice = get_advice(st.session_state["audit_report"])
            st.session_state["advice_report"] = advice
            st.markdown(advice)
        except Exception as e:
            st.error(f"❌ Failed to generate advice: {str(e)}")


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚖️ Lura-Rent")
    st.caption("Privacy-First Legal Auditor")
    st.divider()
    st.success("🟢 Edge AI: Online")
    st.caption(f"Model: `{MODEL_NAME}`")
    st.divider()
    st.info(
        "The AI evaluates the rights of both parties under the "
        "Maharashtra Rent Control Act, 1999 and suggests legal remedies "
        "for risky clauses."
    )

    # Reset button — allows uploading a new document cleanly
    if st.session_state["extracted_text"]:
        st.divider()
        if st.button("🔄 Analyse New Document", use_container_width=True):
            for key in ["extracted_text", "uploaded_filename", "audit_report",
                        "advice_report", "chat_history", "display_chat",
                        "is_generating", "is_getting_advice"]:
                st.session_state[key] = [] if key in ["chat_history", "display_chat"] else ""
            st.session_state["is_generating"] = False
            st.session_state["is_getting_advice"] = False
            st.rerun()


# ── Main Dashboard ────────────────────────────────────────────────────────────
st.title("Document Audit Dashboard")
st.markdown("Upload a standard Indian Residential Rental Agreement to instantly detect unfair clauses and legal risks.")
st.write("")

col1, col2 = st.columns([1.2, 1], gap="large")

with col1:
    st.markdown("### 1. Upload Contract")
    uploaded_file = st.file_uploader("Drag and drop your PDF here", type=["pdf"])

    if uploaded_file:
        # FIX: detect new file by filename — prevents stale text on second upload
        if uploaded_file.name != st.session_state["uploaded_filename"]:
            with st.spinner("Parsing Document Securely..."):
                text = extract_text_from_pdf(uploaded_file)
                if text:
                    st.session_state["extracted_text"] = text
                    st.session_state["uploaded_filename"] = uploaded_file.name
                    # Clear previous results when new file is uploaded
                    st.session_state["audit_report"] = ""
                    st.session_state["advice_report"] = ""
                    st.session_state["chat_history"] = []
                    st.session_state["display_chat"] = []
                    st.session_state["is_generating"] = False
                    st.session_state["is_getting_advice"] = False
                    st.success("✅ Document Loaded Successfully")

        if st.session_state["extracted_text"]:
            with st.expander("📄 View Extracted Text (For verification)"):
                st.text_area(
                    "Raw Text",
                    st.session_state["extracted_text"],
                    height=250,
                    disabled=True
                )

with col2:
    st.markdown("### 2. Analysis Engine")
    if st.session_state["extracted_text"]:
        st.info("Target Model: **Lura-Rent AI (Local)**")
        st.write("")
        if st.button("🚀 Run AI Audit"):
            system_prompt = """You are Lura-Rent, an expert AI Legal Auditor specializing in Indian Residential Rental Agreements under the Maharashtra Rent Control Act, 1999.

Your Goal: Provide a high-level overview of the contract's fairness, followed by a detailed breakdown of the 3 most important clauses.

STRICT OUTPUT RULES:
1. DO NOT use conversational filler like "Here is the summary" or "I can help". Start immediately with the headers.
2. You MUST structure your response EXACTLY like this with empty lines between sections:

### 📋 OVERALL CONTRACT SUMMARY
[Provide a 2-3 sentence overview of the entire agreement. Is it standard, tenant-friendly, or highly landlord-favored?]

### ✅ THE GOOD (Fair Clauses)
* [Bullet point 1: A fair or standard term]
* [Bullet point 2: A fair or standard term]

### ❌ THE BAD (High Risks)
* [Bullet point 1: A highly unfair or illegal term. Explain why it is bad.]
* [Bullet point 2: Another major risk.]

### ⚠️ MIGHT BE A PROBLEM (Gray Areas)
* [Bullet point 1: A vague term that could cause disputes, like maintenance or entry rights.]

---
### 🔍 DETAILED CLAUSE ANALYSIS

**CLAUSE 1:** "[Quote the exact text of the first major issue]"

**RISK LEVEL:** [Low / Medium / High / Critical]

**PLAIN LANGUAGE SUMMARY:** [Explain what this means in simple terms.]

**LEGAL ASSESSMENT:** [Explain if this is enforceable under the Maharashtra Rent Control Act.]

**TENANT ADVISORY:** [What should the tenant do?]

[Repeat the CLAUSE / RISK LEVEL / SUMMARY / ASSESSMENT / ADVISORY format for Clause 2 and Clause 3.]"""

            st.session_state["chat_history"] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Perform a full detailed audit of this rental agreement:\n\n{st.session_state['extracted_text']}"}
            ]
            st.session_state["display_chat"] = []
            st.session_state["audit_report"] = ""
            st.session_state["advice_report"] = ""   # Clear old advice when re-running audit
            st.session_state["is_generating"] = True
    else:
        st.info("Awaiting document upload...")


# ── Results Section ───────────────────────────────────────────────────────────
if st.session_state["extracted_text"]:
    st.divider()
    st.markdown("### 📊 Audit Results")

    # ── Generating audit ──
    if st.session_state["is_generating"]:
        with st.spinner("⏳ Analyzing clauses under Maharashtra Rent Control Act... Please wait."):
            try:
                response = ollama.chat(
                    model=MODEL_NAME,
                    messages=st.session_state["chat_history"],
                    stream=False
                )
                full_response = response['message']['content']

                if full_response:
                    st.session_state["audit_report"] = full_response
                    st.session_state["chat_history"].append(
                        {"role": "assistant", "content": full_response}
                    )
                    # Switch model to conversational mode for follow-up questions
                    st.session_state["chat_history"].append({
                        "role": "system",
                        "content": """The initial audit is complete. You are now a direct, professional legal assistant.
Answer all follow-up questions about the contract concisely and accurately based on the Maharashtra Rent Control Act.

CRITICAL FORMATTING RULES:
1. ALWAYS use bullet points to break down complex information.
2. ALWAYS leave an empty line (double line break) between paragraphs.
3. DO NOT output dense blocks of text. Keep it readable.
4. DO NOT use the rigid "RISK LEVEL / TENANT ADVISORY" format unless explicitly asked.
5. Never use filler phrases like 'I can help'. Start every answer immediately."""
                    })
                    st.session_state["is_generating"] = False
                    st.rerun()

            except Exception as e:
                st.error(f"❌ Failed to connect to model: {str(e)}")
                st.session_state["is_generating"] = False

    # ── Showing audit results ──
    elif st.session_state["audit_report"]:
        st.markdown(st.session_state["audit_report"])

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Action buttons row ──
        btn_col1, btn_col2, btn_col3 = st.columns(3)

        with btn_col1:
            # Next Steps button — NEW
            st.markdown("""
                <div style="background:linear-gradient(135deg,#FEF2F2,#FEE2E2);border:1px solid #FECACA;border-radius:12px;padding:1rem 1.2rem;text-align:center;">
                    <div style="font-size:1.4rem;margin-bottom:0.3rem;">⚡</div>
                    <div style="font-weight:700;font-size:0.95rem;color:#991B1B;margin-bottom:0.2rem;">Risky Clauses Found?</div>
                    <div style="color:#B91C1C;font-size:0.8rem;">Get specific legal remedies and next steps.</div>
                </div>
            """, unsafe_allow_html=True)
            st.write("")
            if st.button("⚡ Advice on Next Steps", use_container_width=True, key="btn_advice"):
                advice_window()

        with btn_col2:
            # Chat button
            st.markdown("""
                <div style="background:linear-gradient(135deg,#ECFDF5,#D1FAE5);border:1px solid #A7F3D0;border-radius:12px;padding:1rem 1.2rem;text-align:center;">
                    <div style="font-size:1.4rem;margin-bottom:0.3rem;">💬</div>
                    <div style="font-weight:700;font-size:0.95rem;color:#064E3B;margin-bottom:0.2rem;">Have Questions?</div>
                    <div style="color:#047857;font-size:0.8rem;">Ask anything about this contract.</div>
                </div>
            """, unsafe_allow_html=True)
            st.write("")
            if st.button("💬 Ask Questions", use_container_width=True, key="btn_chat"):
                chat_window()

        with btn_col3:
            # Export button
            st.markdown("""
                <div style="background:linear-gradient(135deg,#EFF6FF,#DBEAFE);border:1px solid #BFDBFE;border-radius:12px;padding:1rem 1.2rem;text-align:center;">
                    <div style="font-size:1.4rem;margin-bottom:0.3rem;">📥</div>
                    <div style="font-weight:700;font-size:0.95rem;color:#1E3A8A;margin-bottom:0.2rem;">Save Report</div>
                    <div style="color:#1D4ED8;font-size:0.8rem;">Download the full audit as a text file.</div>
                </div>
            """, unsafe_allow_html=True)
            st.write("")

            # Build export content — include advice if already generated
            export_content = st.session_state["audit_report"]
            if st.session_state["advice_report"]:
                export_content += "\n\n" + "="*60 + "\n\nADVICE ON NEXT STEPS\n\n" + "="*60 + "\n\n"
                export_content += st.session_state["advice_report"]

            st.download_button(
                label="📥 Export Full Report",
                data=export_content,
                file_name="Lura_Rent_Audit_Report.txt",
                mime="text/plain",
                use_container_width=True
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()