import os
import streamlit as st
import requests
import pandas as pd

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Clinical Query Copilot",
    page_icon="🏥",
    layout="wide"
)

# ── INJECT CUSTOM CSS ─────────────────────────────────────────────────────
st.markdown("""
    <style>
    /* Hide header anchor links and Streamlit Main Menu / Print options */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp > header {display: none;}
    
    h1 a, h2 a, h3 a, h4 a, h5 a, h6 a {
        display: none !important;
        pointer-events: none !important;
    }
    .st-emotion-cache-10trblm a {
        display: none !important;
    }
    
    /* Make FAQ buttons look more like modern pills */
    div[data-testid="stButton"] button {
        border-radius: 20px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏥 Clinical Query Copilot")
st.markdown("_An AI-powered assistant for clinical queries._")

tab_chat, tab_dash, tab_faq = st.tabs([
    "💬 Chatbot", 
    "📊 Dashboard", 
    "📝 Manage FAQs"
])

# ── TAB 1: CHATBOT ────────────────────────────────────────────────────────
with tab_chat:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Fixed height container so the chat input doesn't "move down" as messages are added
    chat_container = st.container(height=500, border=False)
    
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                if message["role"] == "assistant":
                    if message.get("format_type") == "Table" and isinstance(message.get("content"), list):
                        st.dataframe(pd.DataFrame(message["content"]), use_container_width=True)
                    else:
                        st.markdown(message["content"])
                        
                    if "evidence" in message:
                        with st.expander("🔍 View Evidence & Citations"):
                            st.markdown(message["evidence"])
                else:
                    st.markdown(message["content"])

    if prompt := st.chat_input("Ask a clinical question... (e.g. 'number of patients', 'dosage for Aspirin')"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

        try:
            response = requests.post(f"{API_URL}/api/m18/ask", json={"query": prompt}, timeout=10)
            response.raise_for_status()
            data = response.json()

            answer = data.get("answer", "No answer received.")
            confidence = data.get("confidence_score", 0.0)
            citation = data.get("citation", "Unknown")
            format_type = data.get("format_type", "Text")
            timestamp = data.get("timestamp", "")

            evidence_text = f"**Citation:** {citation}\n\n**Confidence:** {confidence:.0%}\n\n**Format Requested:** {format_type}\n\n*<small>Retrieved at: {timestamp}</small>*"
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": answer, 
                "evidence": evidence_text, 
                "format_type": format_type
            })
            
            with chat_container:
                with st.chat_message("assistant"):
                    if format_type == "Table" and isinstance(answer, list):
                        st.dataframe(pd.DataFrame(answer), use_container_width=True)
                    else:
                        st.markdown(answer)
                    with st.expander("🔍 View Evidence & Citations"):
                        st.markdown(evidence_text, unsafe_allow_html=True)

        except requests.exceptions.ConnectionError:
            st.error("❌ Could not connect to the backend API. Please ensure the backend is running.")
        except Exception as e:
            st.error(f"🚨 An error occurred: {e}")

# ── TAB 2: DASHBOARD ──────────────────────────────────────────────────────
with tab_dash:
    st.subheader("Hospital Overview Dashboard")
    try:
        res = requests.get(f"{API_URL}/api/m18/hospital/stats")
        if res.status_code == 200:
            stats = res.json().get("data", {})
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("👨‍⚕️ Total Doctors", stats.get("Total Doctors", 0))
            col2.metric("🏥 Active Wards", stats.get("Active Wards", 0))
            col3.metric("🛏️ Total Beds", stats.get("Total Beds", 0))
            col4.metric("✅ Available Beds", stats.get("Available Beds", 0))
            
            st.markdown("### 🔬 Specialized Facilities Available")
            facilities = stats.get("Specialized Facilities", [])
            for f in facilities:
                st.markdown(f"- {f}")
        else:
            st.error("Failed to load dashboard stats.")
    except Exception as e:
        st.error(f"Could not connect to backend: {e}")

# ── TAB 3: MANAGE FAQS ────────────────────────────────────────────────────
with tab_faq:
    st.subheader("📝 Manage Clinical FAQs")
    st.markdown("Add, edit, or delete FAQs directly from this list. Changes reflect immediately in the Chatbot.")
    
    # Refresh FAQs
    def fetch_faqs():
        try:
            r = requests.get(f"{API_URL}/api/m18/faqs")
            if r.status_code == 200:
                return r.json().get("data", [])
            return []
        except:
            return []

    # Add FAQ Section
    with st.expander("✨ Add New FAQ", expanded=False):
        with st.form("add_faq_form", clear_on_submit=True):
            col_id, col_cat = st.columns(2)
            with col_id:
                new_id = st.text_input("FAQ ID (e.g. faq_010)")
            with col_cat:
                new_cat = st.selectbox("Category", ["General", "Medication", "Lab Values", "Procedure"])
            new_q = st.text_input("Question")
            new_a = st.text_area("Answer")
            
            if st.form_submit_button("Save FAQ"):
                if new_id and new_q and new_a:
                    res = requests.post(f"{API_URL}/api/m18/faqs", json={
                        "faq_id": new_id, "question_text": new_q, "static_answer": new_a, "category": new_cat
                    })
                    if res.status_code == 200:
                        st.success("FAQ Added Successfully!")
                        st.rerun()
                    else:
                        st.error(res.json().get("detail", "Error adding FAQ"))
                else:
                    st.warning("Please fill out the ID, Question, and Answer fields.")

    st.markdown("---")

    faqs = fetch_faqs()
    if faqs:
        for faq in faqs:
            with st.container(border=True):
                col1, col2, col3 = st.columns([6, 1.5, 1.5])
                with col1:
                    st.markdown(f"**{faq['question_text']}**")
                    st.caption(f"ID: `{faq['faq_id']}` | Category: `{faq['category']}`")
                with col2:
                    if st.button("✏️ Edit", key=f"btn_edit_{faq['faq_id']}", use_container_width=True):
                        st.session_state[f"edit_mode_{faq['faq_id']}"] = not st.session_state.get(f"edit_mode_{faq['faq_id']}", False)
                with col3:
                    if st.button("🗑️ Delete", type="primary", key=f"btn_del_{faq['faq_id']}", use_container_width=True):
                        res = requests.delete(f"{API_URL}/api/m18/faqs/{faq['faq_id']}")
                        if res.status_code == 200:
                            st.rerun()
                        else:
                            st.error("Error deleting FAQ.")
                
                # Inline Edit Form
                if st.session_state.get(f"edit_mode_{faq['faq_id']}", False):
                    with st.form(f"form_edit_{faq['faq_id']}"):
                        e_q = st.text_input("Edit Question", value=faq['question_text'])
                        e_a = st.text_area("Edit Answer", value=faq['static_answer'])
                        
                        categories = ["General", "Medication", "Lab Values", "Procedure"]
                        initial_idx = categories.index(faq['category']) if faq['category'] in categories else 0
                        e_c = st.selectbox("Edit Category", categories, index=initial_idx)
                        
                        if st.form_submit_button("Update FAQ"):
                            payload = {"question_text": e_q, "static_answer": e_a, "category": e_c}
                            res = requests.put(f"{API_URL}/api/m18/faqs/{faq['faq_id']}", json=payload)
                            if res.status_code == 200:
                                st.session_state[f"edit_mode_{faq['faq_id']}"] = False
                                st.success("Updated successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to update.")
    else:
        st.info("No FAQs found or backend is offline.")


