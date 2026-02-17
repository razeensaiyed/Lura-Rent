import streamlit as st
import PyPDF2
import ollama 

# --- Phase 1: Lura-Rent MVP (AI Connected) ---

st.set_page_config(page_title="Lura-Rent MVP", page_icon="⚖️", layout="centered")

# --- Helper Functions ---
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

def analyze_with_ollama(document_text, user_question):
    """
    Sends the document text and user question to the local Ollama model.
    """
    # 1. Construct the Prompt
    # We give the AI a 'persona' so it knows it's a legal auditor.
    system_prompt = """
    You are Lura-Rent, an AI legal auditor for Indian Residential Rental Agreements.
    Your goal is to protect the tenant.
    
    Analyze the provided rental agreement text and answer the user's question.
    If the user asks for a summary, provide a structured summary of key terms (Rent, Deposit, Lock-in).
    
    Strictly base your answer ONLY on the provided text.
    If a clause is missing or vague, mention that explicitly.
    """
    
    user_message = f"""
    Document Text:
    {document_text}
    
    User Question:
    {user_question}
    """

    try:
        # 2. Call the Model (Streaming response for better UX)
        response = ollama.chat(
            model='llama3.2',  # Ensure you have pulled this model!
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message},
            ],
        )
        return response['message']['content']
    except Exception as e:
        return f"Error connecting to Ollama: {str(e)}. \n\nMake sure Ollama is running in the background!"

# --- Main Interface ---

st.title("⚖️ Lura-Rent")
st.caption("Phase 1: Local AI Pipeline Active")

# 1. File Upload
uploaded_file = st.file_uploader("Upload Agreement (PDF)", type=["pdf"])

# Store extracted text in session state
if "extracted_text" not in st.session_state:
    st.session_state["extracted_text"] = ""

if uploaded_file:
    # Extract text only if it's a new file or empty
    if st.session_state["extracted_text"] == "":
        with st.spinner("Extracting text..."):
            text = extract_text_from_pdf(uploaded_file)
            if text:
                st.session_state["extracted_text"] = text
                st.success("✅ Document Loaded")
            else:
                st.error("Could not extract text.")

    # Show a snippet (for confidence)
    with st.expander("View Document Text"):
        st.text(st.session_state["extracted_text"][:1000] + "...")

    st.divider()

    # 2. User Question
    default_question = "Summarize the key risks in this agreement for the tenant."
    user_input = st.text_area("Ask Lura-Rent:", value=default_question, height=100)

    # 3. Analyze Button
    if st.button("🔍 Analyze Document"):
        if st.session_state["extracted_text"]:
            with st.spinner("🤖 Lura-Rent is reading (this may take a moment)..."):
                # Call the AI function
                ai_response = analyze_with_ollama(st.session_state["extracted_text"], user_input)
                
                # Display Result
                st.markdown("### 📝 Audit Report")
                st.markdown(ai_response)
                
                # Success checks
                st.success("Analysis Complete.")
        else:
            st.warning("Please upload a document first.")