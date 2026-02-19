"""
VERITAS - Streamlit Web UI
Enterprise Resume Verification Dashboard
"""
from src.ui.dashboard import run_dashboard

if __name__ == "__main__":
    run_dashboard()


# # --- TAB 2: DEEP-DIVE CHAT ---
# with tab2:
#     st.header("Chat with Veritas")
#     st.caption("Ask specific questions about the candidate's DRDO internship, project complexity, or code quality.")

#     if "messages" not in st.session_state:
#         st.session_state.messages = []

#     for message in st.session_state.messages:
#         with st.chat_message(message["role"]):
#             st.markdown(message["content"])

#     if prompt := st.chat_input("Ex: Verify the ASL Web Navigation project details..."):
#         st.session_state.messages.append({"role": "user", "content": prompt})
#         with st.chat_message("user"):
#             st.markdown(prompt)

#         with st.chat_message("assistant"):
#             with st.status("Veritas Investigating...", expanded=False) as status:
#                 app = build_workflow()
#                 final_state = app.invoke({"question": prompt})
#                 status.update(label="Investigation Complete", state="complete")
            
#             st.markdown(final_state["generation"])
            
#             # Trust Score Footer
#             ts = final_state["trust_score"]
#             color = "green" if ts['score'] > 70 else "red"
#             st.markdown(f"---")
#             st.markdown(f"**Trust Score:** <span style='color:{color}'>{ts['score']}/100</span> | **Status:** {ts['label']}", unsafe_allow_html=True)
#             st.caption(f"Reasoning: {ts['reasoning']}")

#         st.session_state.messages.append({"role": "assistant", "content": final_state["generation"]})