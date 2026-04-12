import streamlit as st
import PyPDF2
import ollama 

# --- Page Configuration ---
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

    /* All buttons base */
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

    /* CTA button override — bigger */
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

    /* Dialog */
    [data-testid="stDialog"] > div { border-radius: 16px !important; overflow: hidden !important; box-shadow: 0 25px 60px rgba(0,0,0,0.18) !important; }

    /* Chat bubbles */
    [data-testid="stChatMessage"] { border-radius: 12px !important; padding: 0.75rem 1rem !important; margin-bottom: 0.5rem !important; border: none !important; box-shadow: none !important; }
    div[class*="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) { background: linear-gradient(135deg, #059669, #047857) !important; color: white !important; margin-left: 10% !important; }
    div[class*="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) { background: #F1F5F9 !important; margin-right: 10% !important; line-height: 1.6 !important;}
    [data-testid="chatAvatarIcon"] { border-radius: 8px !important; }

    /* Chat input */
    [data-testid="stChatInput"] { border-radius: 12px !important; border: 2px solid #E2E8F0 !important; }
    [data-testid="stChatInput"]:focus-within { border-color: #10B981 !important; box-shadow: 0 0 0 3px rgba(16,185,129,0.1) !important; }
    </style>
""", unsafe_allow_html=True)

# --- Logic Layer ---
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

# --- Session State ---
for key, default in {
    "extracted_text": "",
    "audit_report": "",
    "chat_history": [],
    "display_chat": [],
    "is_generating": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- Chat Dialog ---
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
            st.markdown('<div style="text-align:center;color:#94A3B8;padding:3rem 1rem;font-size:0.9rem;">Ask me anything about your rental agreement ↓</div>', unsafe_allow_html=True)
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
                        response = ollama.chat(model='lura-rent-model', messages=st.session_state["chat_history"], stream=False)
                        reply_text = response['message']['content']
                    
                    st.markdown(reply_text)
                    st.session_state["display_chat"].append({"role": "assistant", "content": reply_text})
                    st.session_state["chat_history"].append({"role": "assistant", "content": reply_text})
                except Exception as e:
                    st.error(f"Model Error: {str(e)}")

# --- Sidebar ---
with st.sidebar:
    st.markdown("### ⚖️ Lura-Rent")
    st.caption("Privacy-First Legal Auditor")
    st.divider()
    st.success("🟢 Edge AI: Online")
    st.caption("Running locally via Lura-Rent Custom Model")
    st.info("The AI automatically evaluates the rights of both parties according to the Maharashtra Rent Control Act.")

# --- Main Dashboard ---
st.title("Document Audit Dashboard")
st.markdown("Upload a standard Indian Residential Rental Agreement to instantly detect unfair clauses and legal risks.")
st.write("")

col1, col2 = st.columns([1.2, 1], gap="large")

with col1:
    st.markdown("### 1. Upload Contract")
    uploaded_file = st.file_uploader("Drag and drop your PDF here", type=["pdf"])
    if uploaded_file:
        if st.session_state["extracted_text"] == "":
            with st.spinner("Parsing Document Securely..."):
                text = extract_text_from_pdf(uploaded_file)
                if text:
                    st.session_state["extracted_text"] = text
                    st.success("✅ Document Loaded Successfully")
        with st.expander("📄 View Extracted Text (For verification)"):
            st.text_area("Raw Text", st.session_state["extracted_text"], height=250, disabled=True)

with col2:
    st.markdown("### 2. Analysis Engine")
    if st.session_state["extracted_text"]:
        st.info("Target Model: **Lura-Rent AI (Local)**")
        st.write("")
        if st.button("🚀 Run AI Audit"):
            # ✅ UPDATED PROMPT: Added "The Good, The Bad, Might be a Problem" overview
            system_prompt = """
You are Lura-Rent, an expert AI Legal Auditor specializing in Indian Residential Rental Agreements under the Maharashtra Rent Control Act, 1999.

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

[Repeat the CLAUSE / RISK LEVEL / SUMMARY / ASSESSMENT / ADVISORY format for Clause 2 and Clause 3.]
"""
            st.session_state["chat_history"] = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': f"Perform a full detailed audit of this rental agreement:\n\n{st.session_state['extracted_text']}"}
            ]
            st.session_state["display_chat"] = []
            st.session_state["audit_report"] = ""
            st.session_state["is_generating"] = True
    else:
        st.info("Awaiting document upload...")

# --- Results Section ---
if st.session_state["extracted_text"]:
    st.divider()
    st.markdown("### 📊 Audit Results")

    if st.session_state["is_generating"]:
        with st.spinner("⏳ Analyzing clauses under Maharashtra Rent Control Act... Please wait."):
            try:
                response = ollama.chat(
                    model='lura-rent-model',
                    messages=st.session_state["chat_history"],
                    stream=False
                )
                
                full_response = response['message']['content']

                if full_response:
                    st.session_state["audit_report"] = full_response
                    st.session_state["chat_history"].append({'role': 'assistant', 'content': full_response})
                    
                    # ✅ UPDATED CHATBOT PROMPT: Forced formatting constraints for readablility
                    chatbot_rules = """
                    The initial audit is complete. You are now a direct, professional legal assistant. 
                    Answer all follow-up questions about the contract concisely and accurately based on the Maharashtra Rent Control Act.
                    
                    CRITICAL FORMATTING RULES:
                    1. ALWAYS use bullet points to break down complex information.
                    2. ALWAYS leave an empty line (double line break) between paragraphs.
                    3. DO NOT output dense blocks of text. Keep it readable.
                    4. DO NOT use the rigid "RISK LEVEL / TENANT ADVISORY" format unless explicitly asked. Just answer the question naturally but professionally.
                    5. Never use filler phrases like 'I can help'. Start every answer immediately.
                    """
                    st.session_state["chat_history"].append({
                        'role': 'system',
                        'content': chatbot_rules
                    })
                    st.session_state["is_generating"] = False
                    st.rerun()

            except Exception as e:
                st.error(f"❌ Failed to connect to model: {str(e)}")
                st.session_state["is_generating"] = False

    elif st.session_state["audit_report"]:
        st.markdown(st.session_state["audit_report"])

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
            <div style="background:linear-gradient(135deg,#ECFDF5,#D1FAE5);border:1px solid #A7F3D0;border-radius:12px;padding:1.5rem 2rem;text-align:center;margin:1rem 0 0.5rem 0;">
                <div style="font-size:1.8rem;margin-bottom:0.4rem;">💬</div>
                <div style="font-weight:700;font-size:1.1rem;color:#064E3B;margin-bottom:0.3rem;">Have Questions About This Contract?</div>
                <div style="color:#047857;font-size:0.88rem;">Ask Lura-Rent anything — clause explanations, tenant rights, legal implications under Maharashtra law.</div>
            </div>
        """, unsafe_allow_html=True)

        _, mid, _ = st.columns([1, 2, 1])
        with mid:
            if st.button("💬 Ask Questions About This Contract", use_container_width=True, type="primary"):
                chat_window()

        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()

        _, col_dl, _ = st.columns([1, 1, 1])
        with col_dl:
            st.download_button(
                label="📥 Export Audit Report",
                data=st.session_state["audit_report"],
                file_name="Lura_Rent_Audit_Report.txt",
                mime="text/plain",
                use_container_width=True
            )