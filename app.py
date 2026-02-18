import streamlit as st
import os
import re
from src.agents.graph import build_workflow
from src.utils.ingest import ingest_resume

# --- PAGE CONFIG ---
st.set_page_config(page_title="Veritas: AI Recruiter Audit", page_icon="🕵️‍♂️", layout="wide")

# --- CUSTOM CSS FOR UI ---
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #007BFF;
    }
    .trust-high { color: green; font-weight: bold; }
    .trust-low { color: red; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.title("🕵️‍♂️ Veritas: Automated HR Auditor")
st.markdown("Automated pre-screening, skill verification, and agentic RAG for technical recruitment.")
st.divider()

# --- SIDEBAR: FILE UPLOAD ---
with st.sidebar:
    st.header("📁 Document Ingestion")
    uploaded_file = st.file_uploader("Upload Candidate Resume (PDF)", type="pdf")
    
    if uploaded_file:
        # Create data dir if not exists
        if not os.path.exists("data"):
            os.makedirs("data")
            
        file_path = os.path.join("data", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        if st.button("🚀 Process & Index Resume"):
            with st.spinner("Analyzing structure and creating vector embeddings..."):
                ingest_resume(file_path)
            st.success("Resume Indexing Complete!")
            st.session_state['resume_ready'] = True

# --- MAIN INTERFACE TABS ---
tab1, tab2 = st.tabs(["📋 Automated Audit & ATS", "💬 Deep-Dive Chat"])

# --- TAB 1: AUTOMATED AUDIT ---
with tab1:
    st.header("Candidate Pre-Screening Audit")
    job_description = st.text_area("Paste Job Description (JD) here to calculate ATS Match:", height=150)
    
    if st.button("Run Full Audit"):
        if not uploaded_file:
            st.error("Please upload a resume first.")
        else:
            with st.spinner("Veritas is auditing the candidate..."):
                # Initializing Graph for a specific 'Audit' query
                app = build_workflow()
                
                # Step 1: Automated Skill Consistency Check
                # We send a specific hidden prompt to the agent
                audit_query = f"""Perform a full audit. 
                1. Compare this resume against this JD: {job_description}.
                2. Identify skills mentioned in 'Skills' but missing from 'Projects'.
                3. Check for clickable GitHub/Portfolio links.
                4. Give an ATS Match %."""
                
                result = app.invoke({"question": audit_query})
                
                # --- DISPLAY AUDIT RESULTS ---
                col1, col2, col3 = st.columns(3)
                
                # Mocking ATS for the UI logic - usually derived from LLM output
                with col1:
                    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                    st.metric("ATS Match Score", "85%", "+5% vs average")
                    st.markdown("</div>", unsafe_allow_html=True)
                
                with col2:
                    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                    ts = result["trust_score"]
                    st.metric("Verification Score", f"{ts['score']}/100")
                    st.write(f"**Status:** {ts['label']}")
                    st.markdown("</div>", unsafe_allow_html=True)

                with col3:
                    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                    st.metric("Experience Depth", "Mid-Level", "High potential")
                    st.markdown("</div>", unsafe_allow_html=True)

                st.subheader("🕵️‍♂️ Auditor's Detailed Findings")
                st.write(result["generation"])
                
                st.info(f"**Verification Reasoning:** {ts['reasoning']}")

# --- TAB 2: DEEP-DIVE CHAT ---
with tab2:
    st.header("Chat with Veritas")
    st.caption("Ask specific questions about the candidate's DRDO internship, project complexity, or code quality.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ex: Verify the ASL Web Navigation project details..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.status("Veritas Investigating...", expanded=False) as status:
                app = build_workflow()
                final_state = app.invoke({"question": prompt})
                status.update(label="Investigation Complete", state="complete")
            
            st.markdown(final_state["generation"])
            
            # Trust Score Footer
            ts = final_state["trust_score"]
            color = "green" if ts['score'] > 70 else "red"
            st.markdown(f"---")
            st.markdown(f"**Trust Score:** <span style='color:{color}'>{ts['score']}/100</span> | **Status:** {ts['label']}", unsafe_allow_html=True)
            st.caption(f"Reasoning: {ts['reasoning']}")

        st.session_state.messages.append({"role": "assistant", "content": final_state["generation"]})