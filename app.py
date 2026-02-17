import streamlit as st
import PyPDF2
import ollama 

# --- Phase 2: Lura-Rent Professional UI ---

st.set_page_config(
    page_title="Lura-Rent | AI Auditor",
    page_icon="⚖️",
    layout="wide"  # Changed to 'wide' for a dashboard feel
)

# --- Custom CSS for Professional Look ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #FF4B4B; 
        color: white;
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
    """
    Structured Prompting to force the AI into an 'Auditor' format.
    Refined to prevent 'Lenient' mode from ignoring illegal clauses.
    """
    
    # Define nuances for the prompt
    if sensitivity == "Strict (Pro-Tenant)":
        tone_instruction = "Be extremely critical. Flag ANY restriction on the tenant as a risk. Assume the tenant has zero legal knowledge."
    elif sensitivity == "Lenient":
        tone_instruction = "Focus ONLY on severe financial risks (e.g., losing money). Ignore minor privacy inconveniences or standard inconveniences."
    else: # Standard
        tone_instruction = "Balance the rights of both parties. Flag clear violations of the Maharashtra Rent Control Act."

    # Improved System Prompt
    system_prompt = f"""
    You are Lura-Rent, an expert AI Legal Auditor specializing in Indian Residential Rental Agreements.
    
    Your Goal: Audit the agreement for the tenant.
    Sensitivity Mode: {sensitivity}
    Instruction: {tone_instruction}
    
    OUTPUT FORMAT (Strictly follow this structure):
    
    1. **🚨 CRITICAL RISKS (High Severity):**
       - List clauses that are illegal (e.g., Non-refundable deposit, Eviction without proper notice).
       - Quote the exact text.
    
    2. **⚠️ POTENTIAL ISSUES (Medium Severity):**
       - List clauses that are vague or slightly unfair.
    
    3. **✅ SAFE / GOOD CLAUSES:**
       - Mention standard clauses (e.g., Rent amount, reasonable notice periods).
    
    4. **💡 RECOMMENDATIONS:**
       - Suggest 1-2 specific changes.
    
    IMPORTANT: Even in 'Lenient' mode, NEVER call an illegal clause (like 24-hour eviction) 'Safe'.
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

# Sidebar for Controls 
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2237/2237561.png", width=80) # Placeholder Icon
    st.title("Lura-Rent")
    st.markdown("### ⚙️ Audit Settings")
    
    # Feature: Risk Sensitivity Control
    sensitivity = st.radio(
        "Risk Sensitivity:",
        ["Standard", "Strict (Pro-Tenant)", "Lenient"],
        index=0
    )
    
    st.info("💡 **Tip:** Use 'Strict' mode if you are a student or first-time tenant.")
    st.divider()
    st.caption("Powered by Llama 3.2 (Local)")

# Main Content
st.title("📄 AI Rental Agreement Auditor")
st.markdown("### Upload your draft agreement to detect hidden risks instantly.")

col1, col2 = st.columns([1, 1])

with col1:
    uploaded_file = st.file_uploader("Upload PDF Agreement", type=["pdf"])

    if "extracted_text" not in st.session_state:
        st.session_state["extracted_text"] = ""

    if uploaded_file:
        if st.session_state["extracted_text"] == "":
            with st.spinner("📄 Parsing Document..."):
                text = extract_text_from_pdf(uploaded_file)
                if text:
                    st.session_state["extracted_text"] = text
                    st.success("Document Loaded Successfully")

        # Previewer
        with st.expander("👀 View Extracted Text"):
            st.text_area("Raw Text", st.session_state["extracted_text"], height=200)

with col2:
    st.markdown("#### 🔍 Audit Results")
    
    if st.button("RUN AUDIT"):
        if st.session_state["extracted_text"]:
            with st.spinner("🤖 Analyzing clauses against Indian Law..."):
                # Call AI with the selected sensitivity
                audit_report = analyze_with_ollama(st.session_state["extracted_text"], sensitivity)
                
                # Display Result in a clean box
                st.markdown("---")
                st.markdown(audit_report)
                st.balloons() # Reward for completion
        else:
            st.warning("⚠️ Please upload a document first.")