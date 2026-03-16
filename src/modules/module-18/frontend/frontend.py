import os
import streamlit as st
import requests
import pandas as pd

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Module 18 · QA System",
    page_icon="🧪",
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

    /* Refresh button — premium styling */
    .refresh-btn {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        padding: 9px 22px;
        border: none;
        border-radius: 26px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #fff;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 0.3px;
        cursor: pointer;
        transition: all 0.25s ease;
        text-decoration: none;
        float: right;
        margin-top: 14px;
        box-shadow: 0 2px 10px rgba(102,126,234,0.25);
    }
    .refresh-btn:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        color: #fff;
        box-shadow: 0 4px 18px rgba(102,126,234,0.40);
        transform: translateY(-2px);
    }
    .refresh-btn:active {
        transform: translateY(0);
        box-shadow: 0 1px 6px rgba(102,126,234,0.20);
    }
    </style>
""", unsafe_allow_html=True)

# ── HEADER WITH REFRESH BUTTON ────────────────────────────────────────────
st.markdown(
    '<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
    '  <div>'
    '    <h1 style="margin-bottom:0;">\U0001f9ea Module 18 \u00b7 Question-Answering System</h1>'
    '    <p style="color:#888;margin-top:4px;font-size:15px;">'
    '      3-Tier Clinical QA &nbsp;|&nbsp; FastAPI &nbsp;\u00b7&nbsp; Streamlit &nbsp;\u00b7&nbsp; MongoDB Atlas'
    '    </p>'
    '  </div>'
    '  <a class="refresh-btn" href="/" target="_self">'
    '    \U0001f504 Refresh'
    '  </a>'
    '</div>',
    unsafe_allow_html=True,
)

tab_chat, tab_dash, tab_faq, tab_answers, tab_api = st.tabs([
    "💬 Chatbot", 
    "📊 Dashboard", 
    "📝 Manage FAQs",
    "🎨 Answer Templates",
    "🔌 API Reference"
])

# ── TAB 1: CHATBOT ────────────────────────────────────────────────────────
with tab_chat:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Extract prefill EARLY so we can skip the welcome banner when a query is pending
    prefill = st.session_state.pop("_prefill_query", None)

    # Fixed height container so the chat input doesn’t move down as messages grow
    chat_container = st.container(height=500, border=False)
    
    with chat_container:
        # Show welcome banner ONLY when chat is empty AND no sample query is pending
        if not st.session_state.messages and not prefill:
            st.markdown("""
            <div style="text-align:center; padding: 40px 20px;">
                <h2>👋 Welcome to the QA System</h2>
                <p style="color: #666; font-size: 16px;">
                    Ask questions about medications, lab values, hospital stats, or patient history.<br>
                    The system searches our <strong>FAQ database</strong> and <strong>clinical intent templates</strong> to find answers.
                </p>
            </div>
            """, unsafe_allow_html=True)

            # System status indicators
            scol1, scol2, scol3 = st.columns(3)
            try:
                r = requests.get(f"{API_URL}/api/m18/faqs", timeout=3)
                faq_count = len(r.json().get("data", [])) if r.status_code == 200 else 0
                scol1.success("✅ Backend Online")
                scol2.info(f"📚 {faq_count} FAQs Loaded")
                # Database connectivity check
                try:
                    db_res = requests.get(f"{API_URL}/api/m18/answer_templates", timeout=3)
                    if db_res.status_code == 200:
                        scol3.success("🗄️ Database Connected")
                    else:
                        scol3.error("❌ Database Error")
                except Exception:
                    scol3.error("❌ Database Unreachable")
            except Exception:
                scol1.error("❌ Backend Offline")
                scol2.warning("⚠️ FAQs Unavailable")
                scol3.warning("⚠️ Database Unknown")

            st.markdown("#### 💡 Try asking:")
            qcol1, qcol2 = st.columns(2)
            sample_questions = [
                "What is the standard dosage for Aspirin?",
                "How many doctors are available?",
                "What is a normal resting heart rate?",
                "How do I prepare for an MRI scan?"
            ]
            for i, sq in enumerate(sample_questions):
                col = qcol1 if i % 2 == 0 else qcol2
                if col.button(f"💬 {sq}", key=f"sq_{i}", use_container_width=True):
                    st.session_state["_prefill_query"] = sq
                    st.rerun()
        
        # Render chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                if message["role"] == "assistant":
                    fmt = message.get("format_type", "Text")
                    if fmt == "Table" and isinstance(message.get("content"), list):
                        st.dataframe(pd.DataFrame(message["content"]), use_container_width=True)
                    elif fmt == "Summary":
                        st.info(message["content"])
                    else:
                        st.markdown(message["content"])
                        
                    if "evidence" in message:
                        with st.expander("🔍 View Evidence & Citations"):
                            st.markdown(message["evidence"])
                else:
                    st.markdown(message["content"])

    prompt = prefill or st.chat_input("Ask a clinical question... (e.g. 'number of patients', 'dosage for Aspirin')")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

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
            
        except requests.exceptions.ConnectionError:
            st.session_state.messages.append({
                "role": "assistant",
                "content": "❌ Could not connect to the backend API. Please ensure the backend is running.",
                "format_type": "Text"
            })
        except Exception as e:
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"🚨 An error occurred: {e}",
                "format_type": "Text"
            })
        
        # Rerun so the messages render inside chat_container properly
        st.rerun()

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

# ── TAB 4: ANSWER TEMPLATES ───────────────────────────────────────────────
with tab_answers:
    st.subheader("🎨 Answer Templates Configuration")
    st.markdown("""
    This table shows the **format rules** used by the backend to render answers.
    When a question is matched to an intent, the system looks up the `answer_id`
    foreign key from the question template, then fetches the corresponding
    `format_type` and `display_configuration` from this collection.
    """)
    try:
        res = requests.get(f"{API_URL}/api/m18/answer_templates")
        if res.status_code == 200:
            ans_templates = res.json().get("data", [])
            if ans_templates:
                df = pd.DataFrame(ans_templates)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No answer templates found in database.")
    except Exception as e:
        st.error(f"Could not connect to backend: {e}")

# ── TAB 5: API REFERENCE ──────────────────────────────────────────────────
with tab_api:
    st.subheader("🔌 API Endpoints")

    st.caption(
        "All REST routes used by and exposed from Module 18. "
        f"Full interactive docs → [Swagger UI]({API_URL}/docs) · [ReDoc]({API_URL}/redoc)"
    )

    # ── Internal APIs ──────────────────────────────────────────────
    st.markdown("### 🏥 Module 18 — Internal Endpoints")
    st.markdown("""
| Method | Endpoint | Purpose |
|--------|----------|----------|
| `POST` | `/api/m18/ask` | Submit a clinical query and receive an answer |
| `GET` | `/api/m18/faqs` | List all FAQs from the repository |
| `POST` | `/api/m18/faqs` | Create a new FAQ entry |
| `PUT` | `/api/m18/faqs/{faq_id}` | Update an existing FAQ |
| `DELETE`| `/api/m18/faqs/{faq_id}` | Delete an FAQ |
| `GET` | `/api/m18/faqs/stats` | Aggregation — FAQ count by category |
| `GET` | `/api/m18/templates` | List question intent templates |
| `GET` | `/api/m18/answer_templates` | List answer format templates |
| `GET` | `/api/m18/hospital/stats` | Hospital overview metrics |
| `GET` | `/api/m18/analytics/usage` | Usage analytics (aggregation pipeline) |
""")

    with st.expander("💻 POST /api/m18/ask — Backend Code & Sample"):
        st.markdown(
            "The main QA endpoint. It follows a **3-step process**: "
            "(1) Search FAQs via `$text` index, "
            "(2) Match against intent templates via regex, "
            "(3) Format the answer using `answer_templates` FK lookup."
        )
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Request Body**")
            st.code('{\n  "query": "What is the standard dosage for Aspirin?"\n}', language="json")
        with c2:
            st.markdown("**Response**")
            st.code(
                '{\n'
                '  "answer": "The standard dose is 81 mg to 325 mg...",\n'
                '  "confidence_score": 0.98,\n'
                '  "citation": "FAQ Database \u2013 Medication",\n'
                '  "format_type": "Text",\n'
                '  "timestamp": "2026-03-16T17:30:00Z"\n'
                '}',
                language="json",
            )
        st.markdown("**Backend Implementation (FastAPI)**")
        st.code('''
@app.post("/api/m18/ask")
async def ask_question(request: QueryRequest):
    query = request.query

    # Process 1.0: Search FAQ repository (MongoDB $text index)
    search_results = list(
        faq_repository.find(
            {"$text": {"$search": query}},
            {"score": {"$meta": "textScore"}, ...}
        ).sort([("score", {"$meta": "textScore"})]).limit(1)
    )
    if search_results:
        match = search_results[0]
        return {"answer": match["static_answer"], "confidence_score": 0.98, ...}

    # Process 2.0: Match intent via regex templates
    for template in question_templates.find({}):
        if re.search(template["pattern"], query, re.IGNORECASE):
            # Mock call to Module 17 for clinical data
            mock_answer = get_mock_data(template["data_source_required"])
            return {"answer": mock_answer, "confidence_score": 0.85, ...}

    # Fallback
    return {"answer": "Query not recognized.", "confidence_score": 0.0}
''', language="python")

    with st.expander("💻 GET /api/m18/faqs — Backend Code & Sample"):
        st.markdown("Returns all FAQ documents from `faq_repository`. Excludes the MongoDB internal `_id` field.")
        st.code('''
@app.get("/api/m18/faqs")
async def get_faqs():
    faqs = list(faq_repository.find({}, {"_id": 0}))
    return {"status": "success", "data": faqs}
''', language="python")
        st.markdown("**Sample Response**")
        st.code(
            '{\n  "status": "success",\n  "data": [{"faq_id": "faq_001", "question_text": "...", ...}]\n}',
            language="json",
        )

    with st.expander("💻 GET /api/m18/analytics/usage — Aggregation Pipeline Code"):
        st.markdown("Demonstrates MongoDB **Aggregation Pipeline**: groups `evidence_logs` by `match_type`, counts frequency, and calculates average `confidence_score`.")
        st.code('''
@app.get("/api/m18/analytics/usage")
async def get_usage_analytics():
    pipeline = [
        {
            "$group": {
                "_id": "$match_type",
                "count": {"$sum": 1},
                "avg_confidence": {"$avg": "$confidence_score"}
            }
        },
        {"$sort": {"count": -1}}
    ]
    result = list(evidence_logs.aggregate(pipeline))
    return {"status": "success", "data": result}
''', language="python")

    with st.expander("💻 CRUD Endpoints — Create / Update / Delete FAQ"):
        st.markdown("Standard REST CRUD operations on `faq_repository`:")
        st.code('''
# CREATE
@app.post("/api/m18/faqs")
async def create_faq(faq: FAQCreate):
    if faq_repository.find_one({"faq_id": faq.faq_id}):
        raise HTTPException(400, "FAQ ID already exists.")
    faq_repository.insert_one(faq.dict())
    return {"status": "success", "message": "FAQ created."}

# UPDATE
@app.put("/api/m18/faqs/{faq_id}")
async def update_faq(faq_id: str, faq_update: FAQUpdate):
    update_data = {k: v for k, v in faq_update.dict().items() if v is not None}
    faq_repository.update_one({"faq_id": faq_id}, {"$set": update_data})
    return {"status": "success", "message": "FAQ updated."}

# DELETE
@app.delete("/api/m18/faqs/{faq_id}")
async def delete_faq(faq_id: str):
    faq_repository.delete_one({"faq_id": faq_id})
    return {"status": "success", "message": "FAQ deleted."}
''', language="python")

    st.markdown("---")

    # ── Cross-Module APIs ────────────────────────────────────────
    st.markdown("### 🔗 Cross-Module Integration")
    st.markdown("""
| Direction | Method | Route | Description |
|-----------|--------|-------|-------------|
| **M18 → M17** | `GET` | `/api/m17/clinical-data` | Fetch aggregated clinical data from **Module 17 — Smart Clinical Views** |
| **M18 → M49** | `POST` | `/api/m49/usage-log` | Log every query to **Module 49 — Integrated CDS** |
| **M17 → M18** | `GET` | `/api/m18/ask` | Module 17 can query our QA engine |
| **M49 → M18** | `GET` | `/api/m18/analytics/usage` | Module 49 can pull usage analytics |
""")

    with st.expander("💻 Module 17 integration — Mock implementation & data sources"):
        st.markdown(
            "Module 18 calls Module 17's API to retrieve clinical data based on the "
            "`data_source_required` field from the matched intent template:"
        )
        st.markdown("""
| Data Source | What is returned |
|-------------|------------------|
| `Patient_Records_DB` | Patient demographics, history, diagnoses |
| `Pharmacy_DB` | Medication details, side effects, dosages |
| `Hospital_Analytics_DB` | Symptom trends, recovery statistics |
| `Hospital_Overview_DB` | Doctors, wards, beds, facilities |
""")
        st.code('''
# Current mock implementation in backend.py:
if data_source_required == "Patient_Records_DB":
    mock_answer = "[Module 17] Patient: 45yo male, Type 2 DM, HbA1c 7.2%"
elif data_source_required == "Pharmacy_DB":
    mock_answer = "[Module 17] Metformin: GI upset, nausea. Take with meals."

# Future real integration:
# response = requests.get("http://module17/api/m17/clinical-data",
#     params={"source": data_source_required})
# real_data = response.json()
''', language="python")

    with st.expander("💻 Module 49 integration — Silent async logging"):
        st.markdown(
            "Every query is silently logged to Module 49 via an async background function. "
            "This **never** appears in the user-facing response."
        )
        st.code('''
async def send_log_to_module_49(log_data: dict) -> None:
    """Async background POST to Module 49 (never blocks response)."""
    sanitized = {
        "log_id": log_data.get("log_id"),
        "query": log_data.get("query"),
        "match_type": log_data.get("match_type", "none"),
        "confidence_score": log_data.get("confidence_score", 0.0),
        "source_reference": log_data.get("source_reference", "N/A"),
        "timestamp": str(log_data.get("timestamp", "")),
    }
    print(f"[Module 49 POST /api/m49/usage-log] {json.dumps(sanitized)}")

# Called via: asyncio.ensure_future(send_log_to_module_49(log_entry))
''', language="python")

    st.markdown("---")

    # ── Database layer ──────────────────────────────────────────
    st.markdown("### 🗄️ MongoDB Collections")
    st.markdown("""
| Collection | Primary Key | Purpose |
|------------|-------------|----------|
| `faq_repository` | `faq_id` | Stores clinical FAQ question-answer pairs |
| `question_templates` | `intent` | Regex-based intent matching templates |
| `answer_templates` | `answer_id` | Controls answer rendering format (Text / Table / Summary) |
| `evidence_logs` | `evidence_id` | Audit trail of every query with confidence scores |
""")

    with st.expander("💻 Schema validation & index setup code"):
        st.code('''
# Schema validation (database.py)
faq_validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["faq_id", "question_text", "static_answer", "category", "template_id"],
        "properties": {
            "faq_id":        {"bsonType": "string"},
            "question_text": {"bsonType": "string"},
            "static_answer": {"bsonType": "string"},
            "category":      {"enum": ["Medication", "Lab Values", "General", "Procedure"]},
            "template_id":   {"bsonType": "string"}
        }
    }
}
db.create_collection("faq_repository", validator=faq_validator)

# Text index for full-text search
faq_repository.create_index([("question_text", TEXT)], default_language="english")
''', language="python")
