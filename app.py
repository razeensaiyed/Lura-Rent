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

# --- Modern SaaS CSS Injection (Emerald Green Theme & Animations) ---
st.markdown("""
    <style>
    /* 1. Import Modern Font (Inter) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    /* 2. Hide Streamlit Branding (Kept header visible so sidebar toggle works!) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 3. Fade-in and slide-up animation for the main content */
    @keyframes slideUpFade {
        0% { opacity: 0; transform: translateY(20px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    .block-container {
        animation: slideUpFade 0.6s ease-out forwards;
        padding-top: 2rem !important;
    }

    /* 4. Sidebar Gradient Accent (Emerald Green) */
    [data-testid="stSidebar"]::before {
        content: '';
        display: block;
        height: 4px;
        width: 100%;
        background: linear-gradient(90deg, #10B981, #047857); /* Emerald 500 to 700 */
    }

    /* 5. Dashboard Cards (Floating Columns) */
    [data-testid="column"] {
        background: #FFFFFF;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.05), 0 2px 4px -1px rgba(15, 23, 42, 0.03);
        border: 1px solid #E2E8F0; 
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    [data-testid="column"]:hover {
        box-shadow: 0 10px 15px -3px rgba(15, 23, 42, 0.08), 0 4px 6px -2px rgba(15, 23, 42, 0.04);
    }

    /* 6. Button Animations (Green Theme) */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        background-color: #059669 !important; /* Emerald 600 */
        color: #FFFFFF !important;
        border: none;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px -1px rgba(5, 150, 105, 0.2);
    }
    .stButton > button:hover {
        background-color: #047857 !important; /* Emerald 700 */
        transform: translateY(-2px);
        box-shadow: 0 8px 12px -1px rgba(5, 150, 105, 0.3);
    }
    .stButton > button:active {
        transform: translateY(0);
    }

    /* 7. File Uploader Animations */
    [data-testid="stFileUploadDropzone"] {
        border-radius: 12px;
        border: 2px dashed #A7F3D0 !important; /* Emerald 200 */
        background-color: #F8FAFC !important; 
        transition: all 0.3s ease;
    }
    [data-testid="stFileUploadDropzone"]:hover {
        background-color: #ECFDF5 !important; /* Emerald 50 */
        border-color: #10B981 !important; /* Emerald 500 */
    }
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

def analyze_with_ollama(document_text, sensitivity="Standard"):
    if sensitivity == "Strict (Pro-Tenant)":
        tone_instruction = "Be extremely critical. Flag ANY restriction on the tenant as a High/Critical risk."
    elif sensitivity == "Lenient":
        tone_instruction = "Focus ONLY on severe financial risks. Ignore minor inconveniences."
    else: 
        tone_instruction = "Balance the rights of both parties according to Maharashtra law."

    system_prompt = f"""
    You are Lura-Rent, an expert AI Legal Auditor specializing in Indian Residential Rental Agreements (Maharashtra).
    
    Your Goal: Audit the document and extract the 3 most important clauses to review.
    Sensitivity Mode: {sensitivity}
    Instruction: {tone_instruction}
    
    OUTPUT FORMAT:
    For each of the 3 clauses, you MUST use exactly this Markdown format. You MUST leave an empty line between every single label.
    
    **CLAUSE:** "[Quote the exact 1-2 sentences of the clause from the text]"
    
    **RISK LEVEL:** [Low / Medium / High / Critical]
    
    **PLAIN LANGUAGE SUMMARY:** [Explain what this means in simple terms for a first-time tenant]
    
    **LEGAL ASSESSMENT:** [Assess if this is standard or unlawful under the Maharashtra Rent Control Act]
    
    **TENANT ADVISORY:** [Actionable advice on what the tenant should negotiate or watch out for]
    
    ---
    
    STRICT RULE: Do not bold the word "CLAUSE" incorrectly. Keep the formatting perfectly clean.
    """
    
    user_message = f"Document Text:\n{document_text}"

    try:
        response = ollama.chat(
            model='llama3.2',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message},
            ],
        )
        return response['message']['content']
    except Exception as e:
        return f"Error: {str(e)}"

# --- UI Layer ---

if "extracted_text" not in st.session_state:
    st.session_state["extracted_text"] = ""
if "audit_report" not in st.session_state:
    st.session_state["audit_report"] = ""

# --- Sidebar ---
with st.sidebar:
    st.markdown("### ⚖️ Lura-Rent")
    st.caption("Privacy-First Legal Auditor")
    st.divider()
    
    st.markdown("#### ⚙️ Audit Settings")
    sensitivity = st.radio(
        "Select Risk Sensitivity:",
        ["Standard", "Strict (Pro-Tenant)", "Lenient"],
        index=0,
        help="Adjusts how aggressively the AI flags potential issues."
    )
    
    st.info("💡 **Tip:** Use 'Strict' mode if you are a student or first-time tenant.")
    st.divider()
    st.success("🟢 Edge AI: Online")
    st.caption("Running locally via Llama-3.2-3B")

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
        st.info(f"Target Model: **Llama 3.2 (Local)** \nMode: **{sensitivity}**")
        st.write("") 
        if st.button("🚀 Run AI Audit"):
            with st.spinner("Analyzing clauses against Maharashtra Rent Control Act..."):
                report = analyze_with_ollama(st.session_state["extracted_text"], sensitivity)
                st.session_state["audit_report"] = report
                st.balloons() 
    else:
        st.info("Awaiting document upload...")

# --- Results Section ---
if st.session_state["audit_report"]:
    st.divider()
    st.markdown("### 📊 Audit Results")
    
    with st.container():
        st.markdown(st.session_state["audit_report"])
    
    st.divider()
    
    col_dl1, col_dl2, col_dl3 = st.columns([1, 2, 1])
    with col_dl2:
        st.download_button(
            label="📥 Export Audit Report as TXT",
            data=st.session_state["audit_report"],
            file_name="Lura_Rent_Audit_Report.txt",
            mime="text/plain"
        )