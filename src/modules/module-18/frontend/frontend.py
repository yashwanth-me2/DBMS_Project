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

tab_chat, tab_dash, tab_faqs, tab_answers, tab_api = st.tabs([
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
                        df = pd.DataFrame(message["content"])
                        st.dataframe(df.astype(str), use_container_width=True)
                    elif fmt == "Chart" and isinstance(message.get("content"), list):
                        try:
                            df = pd.DataFrame(message["content"])
                            numeric_cols = df.select_dtypes(include="number").columns.tolist()
                            if numeric_cols:
                                st.bar_chart(df.set_index(df.columns[0])[numeric_cols])
                            else:
                                st.dataframe(df.astype(str), use_container_width=True)
                        except Exception:
                            st.dataframe(pd.DataFrame(message["content"]).astype(str), use_container_width=True)
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
    st.subheader("📊 Comprehensive Project Dashboard")
    st.caption("Toggle each section to explore hospital stats, chatbot internals, queries, and architecture.")

    # ── SECTION 1: Hospital Overview ──────────────────────────────────
    with st.expander("📊 Hospital Overview Dashboard", expanded=True):
        try:
            res = requests.get(f"{API_URL}/api/m18/hospital/stats")
            if res.status_code == 200:
                stats = res.json().get("data", {})
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("👨‍⚕️ Total Doctors", stats.get("Total Doctors", 0))
                col2.metric("🏥 Active Wards", stats.get("Active Wards", 0))
                col3.metric("🛏️ Total Beds", stats.get("Total Beds", 0))
                col4.metric("✅ Available Beds", stats.get("Available Beds", 0))

                st.markdown("**🔬 Specialized Facilities Available**")
                facilities = stats.get("Specialized Facilities", [])
                fac_cols = st.columns(len(facilities) if facilities else 1)
                for i, f in enumerate(facilities):
                    fac_cols[i].success(f"🏥 {f}")
            else:
                st.error("Failed to load dashboard stats.")
        except Exception as e:
            st.error(f"Could not connect to backend: {e}")

    # ── SECTION 2: MongoDB Collections, Schemas & SQL Equivalents ─────
    with st.expander("🗄️ MongoDB Collections, Schemas & Equivalent SQL", expanded=False):
        st.markdown("#### 🗄️ MongoDB Collections & Schemas")

        st.markdown("**1. `faq_repository`** — Stores clinical FAQ question-answer pairs")
        st.code('''# Schema Validation
{
  "$jsonSchema": {
    "bsonType": "object",
    "required": ["faq_id", "question_text", "static_answer", "category", "template_id"],
    "properties": {
      "faq_id":         {"bsonType": "string"},           // Primary Key
      "question_text":  {"bsonType": "string"},           // Searchable (TEXT index)
      "static_answer":  {"bsonType": "string"},
      "category":       {"enum": ["Medication", "Lab Values", "General", "Procedure"]},
      "template_id":    {"bsonType": "string"}            // FK → question_templates.intent
    }
  }
}
// Index: TEXT index on "question_text" for full-text search''', language="javascript")

        st.markdown("**2. `question_templates`** — Regex-based intent matching templates")
        st.code('''# Fields (no formal validator — upserted at startup)
{
  "intent":                "patient_history",              // Primary Key
  "pattern":               "patient.*?history|...",        // Regex pattern
  "query_log_id":          "log_tmpl_01",
  "question_type":         "Temporal",                     // Factual | Statistical | Comparative | Temporal
  "data_source_required":  "Patient_Records_DB",           // Which DB Module 17 queries
  "answer_id":             "ans_tmpl_text"                  // FK → answer_templates.answer_id
}''', language="javascript")

        st.markdown("**3. `answer_templates`** — Controls answer rendering format")
        st.code('''# Schema Validation
{
  "$jsonSchema": {
    "bsonType": "object",
    "required": ["answer_id", "display_configuration", "format_type"],
    "properties": {
      "answer_id":             {"bsonType": "string"},     // Primary Key
      "display_configuration": {"bsonType": "string"},
      "format_type":           {"enum": ["Text", "Table", "Chart", "Summary"]}
    }
  }
}''', language="javascript")

        st.markdown("**4. `evidence_logs`** — Audit trail of every query")
        st.code('''# Schema Validation
{
  "$jsonSchema": {
    "bsonType": "object",
    "required": ["evidence_id", "source_reference", "confidence_score", "timestamp"],
    "properties": {
      "evidence_id":      {"bsonType": "string"},          // Primary Key
      "source_reference": {"bsonType": "string"},
      "confidence_score": {"bsonType": "double"},
      "timestamp":        {"bsonType": "date"}
    }
  }
}''', language="javascript")

        st.markdown("---")
        st.markdown("#### 🔗 Foreign Key Relationships")
        st.markdown("""
| From Collection | Field | → To Collection | Field | Purpose |
|-----------------|-------|-----------------|-------|---------|
| `faq_repository` | `template_id` | → `question_templates` | `intent` | Links FAQ to its intent category |
| `question_templates` | `answer_id` | → `answer_templates` | `answer_id` | Determines answer rendering format |
""")

        st.markdown("---")
        st.markdown("#### 📝 Equivalent SQL Schema (CREATE TABLE Statements)")
        st.code('''-- 1. answer_templates (referenced by question_templates)
CREATE TABLE answer_templates (
    answer_id             VARCHAR(50) PRIMARY KEY,
    display_configuration VARCHAR(255) NOT NULL,
    format_type           ENUM('Text','Table','Chart','Summary') NOT NULL
);

-- 2. question_templates (references answer_templates)
CREATE TABLE question_templates (
    intent                VARCHAR(100) PRIMARY KEY,
    pattern               TEXT NOT NULL,
    query_log_id          VARCHAR(50),
    question_type         ENUM('Factual','Statistical','Comparative','Temporal'),
    data_source_required  VARCHAR(100),
    answer_id             VARCHAR(50),
    FOREIGN KEY (answer_id) REFERENCES answer_templates(answer_id)
);

-- 3. faq_repository (references question_templates)
CREATE TABLE faq_repository (
    faq_id        VARCHAR(50) PRIMARY KEY,
    question_text TEXT NOT NULL,
    static_answer TEXT NOT NULL,
    category      ENUM('Medication','Lab Values','General','Procedure') NOT NULL,
    template_id   VARCHAR(100),
    FOREIGN KEY (template_id) REFERENCES question_templates(intent),
    FULLTEXT INDEX idx_question_text (question_text)
);

-- 4. evidence_logs
CREATE TABLE evidence_logs (
    evidence_id      VARCHAR(50) PRIMARY KEY,
    log_id           VARCHAR(100),
    query            TEXT,
    match_type       VARCHAR(20),
    source_reference VARCHAR(255) NOT NULL,
    confidence_score DOUBLE NOT NULL,
    timestamp        DATETIME NOT NULL
);''', language="sql")

    # ── SECTION 3: All Queries — MongoDB, Python & SQL ─────────────────
    with st.expander("📋 All Queries — MongoDB, Python & SQL Equivalents", expanded=False):
        st.markdown("Every database query used in this project, with **PyMongo (Python)**, **MongoDB Shell**, and **equivalent SQL** code.")
        st.markdown("---")

        # Query 1
        st.markdown("##### Q1. Full-Text Search FAQs (`$text` index)")
        st.markdown("> **Used in:** `POST /api/m18/ask` — Process 1.0 (FAQ matching)")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Python (PyMongo)**")
            st.code('''results = faq_repository.find(
    {"$text": {"$search": query}},
    {"score": {"$meta": "textScore"},
     "faq_id": 1, "question_text": 1,
     "static_answer": 1, "category": 1,
     "template_id": 1}
).sort([("score", {"$meta": "textScore"})]).limit(3)''', language="python")
        with c2:
            st.markdown("**MongoDB Shell**")
            st.code('''db.faq_repository.find(
  { $text: { $search: "dosage Aspirin" } },
  { score: { $meta: "textScore" },
    faq_id: 1, question_text: 1,
    static_answer: 1, category: 1 }
).sort({ score: { $meta: "textScore" } }).limit(3)''', language="javascript")
        st.markdown("**Equivalent SQL**")
        st.code('''SELECT faq_id, question_text, static_answer, category, template_id,
       MATCH(question_text) AGAINST('dosage Aspirin') AS score
FROM faq_repository
WHERE MATCH(question_text) AGAINST('dosage Aspirin')
ORDER BY score DESC
LIMIT 3;''', language="sql")

        st.markdown("---")

        # Query 2
        st.markdown("##### Q2. Regex Keyword Fallback Search")
        st.markdown("> **Used in:** `POST /api/m18/ask` — Process 1.0 fallback")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Python (PyMongo)**")
            st.code('''regex_pattern = "|".join(
    re.escape(k) for k in keywords
)
candidates = faq_repository.find(
    {"question_text": {
        "$regex": regex_pattern,
        "$options": "i"
    }},
    {"faq_id": 1, "question_text": 1,
     "static_answer": 1, "category": 1,
     "template_id": 1}
)''', language="python")
        with c2:
            st.markdown("**MongoDB Shell**")
            st.code('''db.faq_repository.find({
  question_text: {
    $regex: "dosage|aspirin",
    $options: "i"
  }
})''', language="javascript")
        st.markdown("**Equivalent SQL**")
        st.code('''SELECT faq_id, question_text, static_answer, category, template_id
FROM faq_repository
WHERE question_text REGEXP 'dosage|aspirin';''', language="sql")

        st.markdown("---")

        # Query 3
        st.markdown("##### Q3. Get All FAQs")
        st.markdown("> **Used in:** `GET /api/m18/faqs`")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Python (PyMongo)**")
            st.code('faqs = list(faq_repository.find({}, {"_id": 0}))', language="python")
        with c2:
            st.markdown("**MongoDB Shell**")
            st.code('db.faq_repository.find({}, { _id: 0 })', language="javascript")
        st.markdown("**Equivalent SQL**")
        st.code('SELECT faq_id, question_text, static_answer, category, template_id FROM faq_repository;', language="sql")

        st.markdown("---")

        # Query 4
        st.markdown("##### Q4. Create a New FAQ (INSERT)")
        st.markdown("> **Used in:** `POST /api/m18/faqs`")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Python (PyMongo)**")
            st.code('''faq_repository.insert_one({
    "faq_id": "faq_010",
    "question_text": "...",
    "static_answer": "...",
    "category": "Medication",
    "template_id": "qt_med_01"
})''', language="python")
        with c2:
            st.markdown("**MongoDB Shell**")
            st.code('''db.faq_repository.insertOne({
  faq_id: "faq_010",
  question_text: "...",
  static_answer: "...",
  category: "Medication",
  template_id: "qt_med_01"
})''', language="javascript")
        st.markdown("**Equivalent SQL**")
        st.code('''INSERT INTO faq_repository (faq_id, question_text, static_answer, category, template_id)
VALUES ('faq_010', '...', '...', 'Medication', 'qt_med_01');''', language="sql")

        st.markdown("---")

        # Query 5
        st.markdown("##### Q5. Update an Existing FAQ (UPDATE)")
        st.markdown("> **Used in:** `PUT /api/m18/faqs/{faq_id}`")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Python (PyMongo)**")
            st.code('''faq_repository.update_one(
    {"faq_id": faq_id},
    {"$set": {"question_text": "...",
              "static_answer": "..."}}
)''', language="python")
        with c2:
            st.markdown("**MongoDB Shell**")
            st.code('''db.faq_repository.updateOne(
  { faq_id: "faq_001" },
  { $set: { question_text: "...",
            static_answer: "..." } }
)''', language="javascript")
        st.markdown("**Equivalent SQL**")
        st.code('''UPDATE faq_repository
SET question_text = '...', static_answer = '...'
WHERE faq_id = 'faq_001';''', language="sql")

        st.markdown("---")

        # Query 6
        st.markdown("##### Q6. Delete an FAQ (DELETE)")
        st.markdown("> **Used in:** `DELETE /api/m18/faqs/{faq_id}`")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Python (PyMongo)**")
            st.code('faq_repository.delete_one({"faq_id": faq_id})', language="python")
        with c2:
            st.markdown("**MongoDB Shell**")
            st.code('db.faq_repository.deleteOne({ faq_id: "faq_001" })', language="javascript")
        st.markdown("**Equivalent SQL**")
        st.code("DELETE FROM faq_repository WHERE faq_id = 'faq_001';", language="sql")

        st.markdown("---")

        # Query 7
        st.markdown("##### Q7. Check for Duplicate FAQ ID")
        st.markdown("> **Used in:** `POST /api/m18/faqs` — before insert")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Python (PyMongo)**")
            st.code('existing = faq_repository.find_one({"faq_id": faq_id})', language="python")
        with c2:
            st.markdown("**MongoDB Shell**")
            st.code('db.faq_repository.findOne({ faq_id: "faq_010" })', language="javascript")
        st.markdown("**Equivalent SQL**")
        st.code("SELECT * FROM faq_repository WHERE faq_id = 'faq_010' LIMIT 1;", language="sql")

        st.markdown("---")

        # Query 8
        st.markdown("##### Q8. FAQ Count by Category (Aggregation Pipeline)")
        st.markdown("> **Used in:** `GET /api/m18/faqs/stats`")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Python (PyMongo)**")
            st.code('''pipeline = [
    {"$group": {
        "_id": "$category",
        "count": {"$sum": 1}
    }}
]
result = list(
    faq_repository.aggregate(pipeline)
)''', language="python")
        with c2:
            st.markdown("**MongoDB Shell**")
            st.code('''db.faq_repository.aggregate([
  { $group: {
      _id: "$category",
      count: { $sum: 1 }
  }}
])''', language="javascript")
        st.markdown("**Equivalent SQL**")
        st.code('''SELECT category, COUNT(*) AS count
FROM faq_repository
GROUP BY category;''', language="sql")

        st.markdown("---")

        # Query 9
        st.markdown("##### Q9. Get All Question Templates")
        st.markdown("> **Used in:** `GET /api/m18/templates`")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Python (PyMongo)**")
            st.code('templates = list(question_templates.find({}, {"_id": 0}))', language="python")
        with c2:
            st.markdown("**MongoDB Shell**")
            st.code('db.question_templates.find({}, { _id: 0 })', language="javascript")
        st.markdown("**Equivalent SQL**")
        st.code('SELECT intent, pattern, query_log_id, question_type, data_source_required, answer_id FROM question_templates;', language="sql")

        st.markdown("---")

        # Query 10
        st.markdown("##### Q10. Find Question Template by Intent (FK Lookup)")
        st.markdown("> **Used in:** `POST /api/m18/ask` — Process 3.0 (answer format resolution)")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Python (PyMongo)**")
            st.code('''qt_doc = question_templates.find_one(
    {"intent": template_id}
)''', language="python")
        with c2:
            st.markdown("**MongoDB Shell**")
            st.code('''db.question_templates.findOne({
  intent: "medication_guidance"
})''', language="javascript")
        st.markdown("**Equivalent SQL**")
        st.code("SELECT * FROM question_templates WHERE intent = 'medication_guidance';", language="sql")

        st.markdown("---")

        # Query 11
        st.markdown("##### Q11. Get All Answer Templates")
        st.markdown("> **Used in:** `GET /api/m18/answer_templates`")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Python (PyMongo)**")
            st.code('templates = list(answer_templates.find({}, {"_id": 0}))', language="python")
        with c2:
            st.markdown("**MongoDB Shell**")
            st.code('db.answer_templates.find({}, { _id: 0 })', language="javascript")
        st.markdown("**Equivalent SQL**")
        st.code('SELECT answer_id, display_configuration, format_type FROM answer_templates;', language="sql")

        st.markdown("---")

        # Query 12
        st.markdown("##### Q12. FK Lookup — Answer Template by answer_id")
        st.markdown("> **Used in:** `POST /api/m18/ask` — Process 3.0 (determines Text/Table/Chart/Summary)")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Python (PyMongo)**")
            st.code('''ans_doc = answer_templates.find_one(
    {"answer_id": qt_doc["answer_id"]}
)
format_type = ans_doc["format_type"]''', language="python")
        with c2:
            st.markdown("**MongoDB Shell**")
            st.code('''db.answer_templates.findOne({
  answer_id: "ans_tmpl_table"
})''', language="javascript")
        st.markdown("**Equivalent SQL**")
        st.code("SELECT * FROM answer_templates WHERE answer_id = 'ans_tmpl_table';", language="sql")

        st.markdown("---")

        # Query 13
        st.markdown("##### Q13. Insert Evidence Log (Audit Trail)")
        st.markdown("> **Used in:** `POST /api/m18/ask` — after every query resolution")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Python (PyMongo)**")
            st.code('''evidence_logs.insert_one({
    "log_id": str(uuid.uuid4()),
    "evidence_id": "ev_abc123",
    "query": query,
    "match_type": "exact",
    "source_reference": "FAQ Repository",
    "confidence_score": 0.98,
    "timestamp": datetime.utcnow()
})''', language="python")
        with c2:
            st.markdown("**MongoDB Shell**")
            st.code('''db.evidence_logs.insertOne({
  log_id: "...",
  evidence_id: "ev_abc123",
  query: "dosage for Aspirin",
  match_type: "exact",
  source_reference: "FAQ Repository",
  confidence_score: 0.98,
  timestamp: new Date()
})''', language="javascript")
        st.markdown("**Equivalent SQL**")
        st.code('''INSERT INTO evidence_logs (evidence_id, log_id, query, match_type, source_reference, confidence_score, timestamp)
VALUES ('ev_abc123', UUID(), 'dosage for Aspirin', 'exact', 'FAQ Repository', 0.98, NOW());''', language="sql")

        st.markdown("---")

        # Query 14
        st.markdown("##### Q14. Usage Analytics — Aggregation Pipeline (GROUP BY + AVG)")
        st.markdown("> **Used in:** `GET /api/m18/analytics/usage`")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Python (PyMongo)**")
            st.code('''pipeline = [
    {"$group": {
        "_id": "$match_type",
        "count": {"$sum": 1},
        "avg_confidence": {
            "$avg": "$confidence_score"
        }
    }},
    {"$sort": {"count": -1}}
]
result = list(
    evidence_logs.aggregate(pipeline)
)''', language="python")
        with c2:
            st.markdown("**MongoDB Shell**")
            st.code('''db.evidence_logs.aggregate([
  { $group: {
      _id: "$match_type",
      count: { $sum: 1 },
      avg_confidence: {
        $avg: "$confidence_score"
      }
  }},
  { $sort: { count: -1 } }
])''', language="javascript")
        st.markdown("**Equivalent SQL**")
        st.code('''SELECT match_type, COUNT(*) AS count,
       AVG(confidence_score) AS avg_confidence
FROM evidence_logs
GROUP BY match_type
ORDER BY count DESC;''', language="sql")

        st.markdown("---")

        # Query 15
        st.markdown("##### Q15. Schema Validation (Collection Creation)")
        st.markdown("> **Used in:** `database.py` — `setup_database()` function")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Python (PyMongo)**")
            st.code('''db.create_collection(
    "faq_repository",
    validator=faq_validator
)
# Or modify existing
db.command(
    "collMod", "faq_repository",
    validator=faq_validator
)''', language="python")
        with c2:
            st.markdown("**MongoDB Shell**")
            st.code('''db.createCollection("faq_repository", {
  validator: { $jsonSchema: { ... } }
})
db.runCommand({
  collMod: "faq_repository",
  validator: { $jsonSchema: { ... } }
})''', language="javascript")
        st.markdown("**Equivalent SQL**")
        st.code('''CREATE TABLE faq_repository (
    faq_id VARCHAR(50) PRIMARY KEY,
    question_text TEXT NOT NULL,
    static_answer TEXT NOT NULL,
    category ENUM('Medication','Lab Values','General','Procedure') NOT NULL,
    template_id VARCHAR(100) REFERENCES question_templates(intent)
);''', language="sql")

        st.markdown("---")

        # Query 16
        st.markdown("##### Q16. Text Index Creation")
        st.markdown("> **Used in:** `database.py` — enables `$text` search on FAQ questions")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Python (PyMongo)**")
            st.code('''from pymongo import TEXT
faq_repository.create_index(
    [("question_text", TEXT)],
    default_language="english"
)''', language="python")
        with c2:
            st.markdown("**MongoDB Shell**")
            st.code('''db.faq_repository.createIndex(
  { question_text: "text" },
  { default_language: "english" }
)''', language="javascript")
        st.markdown("**Equivalent SQL**")
        st.code('ALTER TABLE faq_repository ADD FULLTEXT INDEX idx_question_text (question_text);', language="sql")

        st.markdown("---")

        # Query 17
        st.markdown("##### Q17. Bulk Insert FAQs")
        st.markdown("> **Used in:** `database.py` & `seed_faqs.py` — initial data seeding")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Python (PyMongo)**")
            st.code('''faq_repository.insert_many([
    {"faq_id": "faq_001",
     "question_text": "...",
     "static_answer": "...",
     "category": "Medication",
     "template_id": "qt_med_01"},
    # ... more documents
])''', language="python")
        with c2:
            st.markdown("**MongoDB Shell**")
            st.code('''db.faq_repository.insertMany([
  { faq_id: "faq_001",
    question_text: "...",
    static_answer: "...",
    category: "Medication",
    template_id: "qt_med_01" },
  // ... more documents
])''', language="javascript")
        st.markdown("**Equivalent SQL**")
        st.code('''INSERT INTO faq_repository (faq_id, question_text, static_answer, category, template_id)
VALUES
  ('faq_001', '...', '...', 'Medication', 'qt_med_01'),
  ('faq_002', '...', '...', 'Lab Values', 'qt_lab_01'),
  ('faq_003', '...', '...', 'General', 'qt_gen_01');''', language="sql")

        st.markdown("---")

        # Query 18
        st.markdown("##### Q18. Upsert Question Templates (INSERT OR UPDATE)")
        st.markdown("> **Used in:** `database.py` — inserts or updates templates at startup")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Python (PyMongo)**")
            st.code('''question_templates.update_one(
    {"intent": template["intent"]},
    {"$set": template},
    upsert=True   # Insert if not exists
)''', language="python")
        with c2:
            st.markdown("**MongoDB Shell**")
            st.code('''db.question_templates.updateOne(
  { intent: "patient_history" },
  { $set: { pattern: "...", ... } },
  { upsert: true }
)''', language="javascript")
        st.markdown("**Equivalent SQL**")
        st.code('''INSERT INTO question_templates (intent, pattern, query_log_id, question_type, data_source_required, answer_id)
VALUES ('patient_history', '...', 'log_tmpl_01', 'Temporal', 'Patient_Records_DB', 'ans_tmpl_text')
ON DUPLICATE KEY UPDATE
  pattern = VALUES(pattern),
  query_log_id = VALUES(query_log_id),
  question_type = VALUES(question_type),
  data_source_required = VALUES(data_source_required),
  answer_id = VALUES(answer_id);''', language="sql")

    # ── SECTION 5: Triggers & Procedures ──────────────────────────────
    with st.expander("⚙️ Triggers & Procedures (MongoDB Equivalents)", expanded=False):
        st.markdown("""
MongoDB does not have traditional SQL-style triggers or stored procedures.
However, this project implements **equivalent patterns** that serve the same purpose:
""")
        st.markdown("---")

        st.markdown("##### 🔔 Trigger 1: Module 49 Silent Logger (≈ `AFTER INSERT` Trigger)")
        st.markdown("""
> **Equivalent to:** SQL `AFTER INSERT ON queries` trigger
>
> Every time a query is processed via `/api/m18/ask`, an **async background task**
> fires and sends the log data to Module 49. This runs silently — it never blocks
> the API response and output goes only to the server terminal.
""")
        st.code('''# backend.py — Async background logger (fires on EVERY /ask call)
async def send_log_to_module_49(log_data: dict) -> None:
    """Simulate async POST to Module 49 (never blocks response)."""
    await asyncio.sleep(0)  # Yield to event-loop
    sanitized = {
        "log_id": log_data.get("log_id"),
        "query": log_data.get("query"),
        "match_type": log_data.get("match_type", "none"),
        "confidence_score": log_data.get("confidence_score", 0.0),
        "source_reference": log_data.get("source_reference", "N/A"),
        "timestamp": str(log_data.get("timestamp", "")),
    }
    print(f"[Module 49 POST /api/m49/usage-log] {json.dumps(sanitized)}")

# Called via:
asyncio.ensure_future(send_log_to_module_49(log_entry))''', language="python")

        st.markdown("---")

        st.markdown("##### 🛡️ Trigger 2: Schema Validation (≈ `BEFORE INSERT` / `CHECK` Constraint)")
        st.markdown("""
> **Equivalent to:** SQL `CHECK` constraint or `BEFORE INSERT` trigger
>
> MongoDB schema validators reject any document that doesn't match the defined
> `$jsonSchema`. This runs **automatically before every insert/update**.
""")
        st.code('''# database.py — Schema validation acts as BEFORE INSERT trigger
faq_validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["faq_id", "question_text", "static_answer",
                     "category", "template_id"],
        "properties": {
            "category": {
                "enum": ["Medication", "Lab Values", "General", "Procedure"]
            }
            # ... other field constraints
        }
    }
}
# Applied at collection creation / modification:
db.create_collection("faq_repository", validator=faq_validator)
# If a document violates the schema → MongoDB raises WriteError''', language="python")

        st.markdown("---")

        st.markdown("##### 🚀 Procedure 1: Lifespan Startup Hook (≈ Stored Procedure)")
        st.markdown("""
> **Equivalent to:** SQL Stored Procedure executed at server startup
>
> The FastAPI `lifespan` context manager runs `setup_database()` once when the
> server starts. This creates collections, applies validators, creates indexes,
> and seeds initial data — all in one atomic operation.
""")
        st.code('''# backend.py — Lifespan hook (runs once on server boot)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run DB setup once when the server starts."""
    try:
        setup_database()  # Creates collections, indexes, seeds data
    except Exception as e:
        print(f"WARNING: DB setup failed: {e}")
    yield

app = FastAPI(title="Clinical Query Copilot API", lifespan=lifespan)''', language="python")

        st.markdown("---")

        st.markdown("##### 🔄 Procedure 2: Upsert Pattern (≈ `INSERT OR UPDATE` Procedure)")
        st.markdown("""
> **Equivalent to:** SQL `MERGE` / `INSERT ... ON DUPLICATE KEY UPDATE`
>
> Question templates use MongoDB's `upsert=True` flag to insert new templates
> or update existing ones based on the `intent` field. This ensures idempotent
> seeding — running it multiple times won't create duplicates.
""")
        st.code('''# database.py — Upsert pattern for question templates
for template in default_templates:
    question_templates.update_one(
        {"intent": template["intent"]},   # Match condition
        {"$set": template},               # Update fields
        upsert=True                       # Insert if not found
    )''', language="python")

        st.markdown("---")

        st.markdown("##### 📊 Procedure 3: Aggregation Pipeline (≈ Stored Procedure with GROUP BY)")
        st.markdown("""
> **Equivalent to:** SQL Stored Procedure with `GROUP BY` and `AVG()`
>
> The analytics endpoint uses MongoDB's aggregation pipeline to compute
> real-time statistics from `evidence_logs`.
""")
        st.code('''# backend.py — Aggregation pipeline (equivalent to stored procedure)
pipeline = [
    {"$group": {
        "_id": "$match_type",
        "count": {"$sum": 1},
        "avg_confidence": {"$avg": "$confidence_score"}
    }},
    {"$sort": {"count": -1}}
]
result = list(evidence_logs.aggregate(pipeline))

# SQL Equivalent:
# SELECT match_type, COUNT(*) as count,
#        AVG(confidence_score) as avg_confidence
# FROM evidence_logs
# GROUP BY match_type
# ORDER BY count DESC''', language="python")

# ── TAB 3: MANAGE FAQS ────────────────────────────────────────────────────
with tab_faqs:
    st.subheader("📝 Manage Knowledge Base FAQs")
    st.markdown("Add, edit, or delete Question-Answer pairs from the FAQ repository.")
    
    # Session state for FAQ edit mode
    if "faq_edit_mode" not in st.session_state:
        st.session_state.faq_edit_mode = False
    if "faq_edit_data" not in st.session_state:
        st.session_state.faq_edit_data = {}

    # Fetch existing FAQs
    try:
        res = requests.get(f"{API_URL}/api/m18/faqs")
        faqs = res.json().get("data", []) if res.status_code == 200 else []
    except Exception:
        faqs = []

    # Two columns: List of FAQs on left, Form on right
    l_col, r_col = st.columns([2, 1])

    with l_col:
        st.markdown("#### 📚 Current FAQs")
        if faqs:
            df = pd.DataFrame(faqs)
            
            # Interactive selection for edit/delete
            st.dataframe(
                df, 
                use_container_width=True, 
                height=400,
                hide_index=True
            )
            
            st.markdown("💡 *To edit or delete an FAQ, enter its ID in the form on the right.*")
        else:
            st.info("No FAQs found in database.")

    with r_col:
        action = st.radio("Action", ["➕ Add New FAQ", "✏️ Edit / Delete FAQ"], horizontal=True)
        
        # Ensure we have templates to choose from
        template_ids = []
        try:
            t_res = requests.get(f"{API_URL}/api/m18/templates")
            if t_res.status_code == 200:
                template_ids = [t["intent"] for t in t_res.json().get("data", [])]
        except Exception:
            pass
            
        categories = ["Medication", "Lab Values", "General", "Procedure"]

        if action == "➕ Add New FAQ":
            with st.form("add_faq_form", clear_on_submit=True):
                new_id = st.text_input("FAQ ID (e.g., faq_001)", placeholder="Must be unique")
                new_q = st.text_area("Question", placeholder="e.g., How to take Aspirin?")
                new_a = st.text_area("Answer", placeholder="e.g., Take one pill daily with food.")
                new_cat = st.selectbox("Category", categories)
                
                # Fetch templates for dropdown if they exist, else allow text input
                if template_ids:
                    new_tmpl = st.selectbox("Intent Template", template_ids)
                else:
                    new_tmpl = st.text_input("Intent Template ID")
                
                submitted = st.form_submit_button("Submit FAQ", use_container_width=True, type="primary")
                
                if submitted:
                    if new_id and new_q and new_a and new_tmpl:
                        payload = {
                            "faq_id": new_id,
                            "question_text": new_q,
                            "static_answer": new_a,
                            "category": new_cat,
                            "template_id": new_tmpl
                        }
                        try:
                            # st.toast guarantees a notification without needing full page reload output
                            post_res = requests.post(f"{API_URL}/api/m18/faqs", json=payload)
                            if post_res.status_code == 200:
                                st.success(f"Successfully added FAQ: {new_id}")
                                st.rerun()  # Refresh the page to update table
                            else:
                                err = post_res.json().get("detail", "Error adding FAQ")
                                st.error(err)
                        except Exception as e:
                            st.error(f"Connection error: {e}")
                    else:
                        st.warning("All fields are required.")
                        
        else:  # Edit / Delete mode
            with st.container(border=True):
                st.markdown("#### Edit or Delete FAQ")
                
                # Search for FAQ ID to edit
                edit_id = st.text_input("Enter FAQ ID to manage")
                
                # Find the target FAQ in our local list if ID is provided
                target_faq = next((f for f in faqs if f.get("faq_id") == edit_id), None)
                
                if edit_id and not target_faq:
                    st.warning(f"No FAQ found with ID '{edit_id}'")
                    
                if target_faq:
                    with st.form("edit_faq_form"):
                        st.info(f"Editing: {edit_id}")
                        e_q = st.text_area("Question", value=target_faq.get("question_text", ""))
                        e_a = st.text_area("Answer", value=target_faq.get("static_answer", ""))
                        
                        e_cat_idx = categories.index(target_faq.get("category")) if target_faq.get("category") in categories else 0
                        e_cat = st.selectbox("Category", categories, index=e_cat_idx)
                        
                        tmpl_val = target_faq.get("template_id", "")
                        if template_ids:
                            e_tmpl_idx = template_ids.index(tmpl_val) if tmpl_val in template_ids else 0
                            e_tmpl = st.selectbox("Intent Template", template_ids, index=e_tmpl_idx)
                        else:
                            e_tmpl = st.text_input("Intent Template ID", value=tmpl_val)
                            
                        col_upd, col_del = st.columns(2)
                        with col_upd:
                            update_btn = st.form_submit_button("Update FAQ", type="primary", use_container_width=True)
                        with col_del:
                            delete_btn = st.form_submit_button("Delete FAQ", use_container_width=True)
                            
                        if update_btn:
                            payload = {
                                "faq_id": edit_id,
                                "question_text": e_q,
                                "static_answer": e_a,
                                "category": e_cat,
                                "template_id": e_tmpl
                            }
                            try:
                                put_res = requests.put(f"{API_URL}/api/m18/faqs/{edit_id}", json=payload)
                                if put_res.status_code == 200:
                                    st.success("Successfully updated FAQ.")
                                    st.rerun()
                                else:
                                    st.error("Failed to update FAQ.")
                            except Exception as e:
                                st.error(f"Error: {e}")
                                
                        if delete_btn:
                            try:
                                del_res = requests.delete(f"{API_URL}/api/m18/faqs/{edit_id}")
                                if del_res.status_code == 200:
                                    st.success("Successfully deleted FAQ.")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete FAQ.")
                            except Exception as e:
                                st.error(f"Error: {e}")

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
# Realistic API call + mock fallback (backend.py):
def fetch_module_17_data(intent_type, parsed_entities):
    try:
        resp = requests.get(
            "http://module17-api:8080/data",
            params={"intent": intent_type, "source": parsed_entities.get("data_source")},
            timeout=2,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException:
        # Mock fallback when Module 17 is unavailable
        if intent_type == "comparative_analysis":
            return [
                {"Metric": "Avg Recovery Days", "Aspirin": 4.2, "Ibuprofen": 3.8},
                {"Metric": "Side Effect Rate", "Aspirin": "12%", "Ibuprofen": "18%"},
            ]
        elif intent_type == "statistical_query":
            return [
                {"Symptom": "Fever", "Count": 142, "Avg_Recovery_Days": 3.2},
                {"Symptom": "Cough", "Count": 89, "Avg_Recovery_Days": 5.1},
            ]
        # ... more intent-specific mocks ...
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
