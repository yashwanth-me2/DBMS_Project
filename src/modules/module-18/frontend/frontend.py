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

    /* Refresh button — clean, subtle styling */
    .refresh-btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 18px;
        border: 1.5px solid #667eea;
        border-radius: 10px;
        background: transparent;
        color: #667eea;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 0.3px;
        cursor: pointer;
        transition: all 0.2s ease;
        text-decoration: none;
        float: right;
        margin-top: 14px;
    }
    .refresh-btn:hover {
        background: #667eea;
        color: #fff;
        box-shadow: 0 2px 12px rgba(102,126,234,0.30);
        transform: translateY(-1px);
    }
    .refresh-btn:active {
        transform: translateY(0);
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
    '    Refresh'
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
    # ── Custom CSS for FAQ cards ──
    st.markdown("""
    <style>
    .faq-header {
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 8px;
    }
    .faq-header h2 { margin: 0; font-size: 22px; }
    .faq-stats-bar {
        display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 18px;
    }
    .faq-stat-chip {
        display: inline-flex; align-items: center; gap: 5px;
        padding: 6px 16px; border-radius: 20px; font-size: 13px;
        font-weight: 600; letter-spacing: 0.2px;
    }
    .faq-card-top {
        display: flex; justify-content: space-between; align-items: flex-start;
        margin-bottom: 8px;
    }
    .faq-id-badge {
        font-size: 11px; font-weight: 700; padding: 3px 10px;
        border-radius: 8px; letter-spacing: 0.5px;
        background: rgba(102,126,234,0.15); color: #5b7bd5;
    }
    .faq-cat-badge {
        font-size: 11px; font-weight: 600; padding: 3px 12px;
        border-radius: 12px; letter-spacing: 0.3px;
    }
    .cat-medication { background: rgba(220,80,80,0.12); color: #c94444; }
    .cat-lab-values { background: rgba(60,160,200,0.12); color: #2e8eb0; }
    .cat-general    { background: rgba(60,180,120,0.12); color: #2ea06a; }
    .cat-procedure  { background: rgba(200,170,60,0.12); color: #a08c2e; }
    .faq-question {
        font-size: 15px; font-weight: 600; margin-bottom: 6px;
        line-height: 1.4;
    }
    .faq-answer {
        font-size: 13.5px; opacity: 0.7;
        line-height: 1.55;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Session state ──
    if "faq_editing_id" not in st.session_state:
        st.session_state.faq_editing_id = None

    # ── Fetch FAQs ──
    try:
        res = requests.get(f"{API_URL}/api/m18/faqs")
        faqs = res.json().get("data", []) if res.status_code == 200 else []
    except Exception:
        faqs = []

    # ── Fetch templates for edit form ──
    template_ids = []
    try:
        t_res = requests.get(f"{API_URL}/api/m18/templates")
        if t_res.status_code == 200:
            template_ids = [t["intent"] for t in t_res.json().get("data", [])]
    except Exception:
        pass
    categories = ["Medication", "Lab Values", "General", "Procedure"]

    # ── Header & stats ──
    st.markdown('<div class="faq-header"><h2>Knowledge Base FAQs</h2></div>', unsafe_allow_html=True)

    # Category color mapping
    cat_colors = {
        "Medication": ("💊", "#f28b8b", "rgba(234,102,102,0.12)"),
        "Lab Values": ("🧪", "#7dd4e8", "rgba(102,200,234,0.12)"),
        "General":    ("📋", "#7de8a8", "rgba(102,234,162,0.12)"),
        "Procedure":  ("🔬", "#e8d47d", "rgba(234,200,102,0.12)"),
    }
    # Count per category
    cat_counts = {}
    for f in faqs:
        c = f.get("category", "General")
        cat_counts[c] = cat_counts.get(c, 0) + 1

    chips_html = ""
    for cat, count in cat_counts.items():
        icon, color, bg = cat_colors.get(cat, ("📋", "#aaa", "rgba(255,255,255,0.06)"))
        chips_html += f'<span class="faq-stat-chip" style="background:{bg};color:{color};">{icon} {cat}: {count}</span>'
    total_chip = f'<span class="faq-stat-chip" style="background:rgba(102,126,234,0.12);color:#8ea4f7;">📚 Total: {len(faqs)}</span>'
    st.markdown(f'<div class="faq-stats-bar">{total_chip}{chips_html}</div>', unsafe_allow_html=True)

    # ── Search & Filter ──
    filter_col1, filter_col2 = st.columns([3, 1])
    with filter_col1:
        search_q = st.text_input("🔍 Search FAQs", placeholder="Type to search questions or answers...", label_visibility="collapsed")
    with filter_col2:
        filter_cat = st.selectbox("Filter", ["All Categories"] + categories, label_visibility="collapsed")

    # Apply filters
    filtered_faqs = faqs
    if search_q:
        sq_lower = search_q.lower()
        filtered_faqs = [f for f in filtered_faqs if sq_lower in f.get("question_text", "").lower() or sq_lower in f.get("static_answer", "").lower()]
    if filter_cat != "All Categories":
        filtered_faqs = [f for f in filtered_faqs if f.get("category") == filter_cat]

    st.caption(f"Showing {len(filtered_faqs)} of {len(faqs)} FAQs")

    # ── FAQ Cards ──
    if not filtered_faqs:
        st.info("No FAQs match your search criteria." if search_q or filter_cat != "All Categories" else "No FAQs found in database.")
    else:
        for idx, faq in enumerate(filtered_faqs):
            faq_id = faq.get("faq_id", "")
            cat = faq.get("category", "General")
            cat_class = cat.lower().replace(" ", "-")
            icon, _, _ = cat_colors.get(cat, ("📋", "#aaa", ""))

            # ── Streamlit Container Card ──
            with st.container(border=True):
                st.markdown(f"""
                <div class="faq-card-top">
                    <span class="faq-id-badge">{faq_id}</span>
                    <span class="faq-cat-badge cat-{cat_class}">{cat}</span>
                </div>
                <div class="faq-question">{faq.get("question_text", "")}</div>
                <div class="faq-answer">{faq.get("static_answer", "")}</div>
                """, unsafe_allow_html=True)

                # ── Edit button (inside the native container) ──
                if st.session_state.faq_editing_id != faq_id:
                    if st.button("Edit", key=f"edit_{faq_id}_{idx}", help=f"Edit {faq_id}"):
                        st.session_state.faq_editing_id = faq_id
                        st.rerun()

            # ── Inline Edit Form ──
            if st.session_state.faq_editing_id == faq_id:
                with st.form(f"edit_form_{faq_id}"):
                    e_q = st.text_area("Question", value=faq.get("question_text", ""), key=f"eq_{faq_id}")
                    e_a = st.text_area("Answer", value=faq.get("static_answer", ""), key=f"ea_{faq_id}")
                    e_cat_idx = categories.index(cat) if cat in categories else 0
                    e_cat = st.selectbox("Category", categories, index=e_cat_idx, key=f"ec_{faq_id}")

                    save_col, cancel_col = st.columns(2)
                    with save_col:
                        save_btn = st.form_submit_button("Save", type="primary", use_container_width=True)
                    with cancel_col:
                        cancel_btn = st.form_submit_button("Cancel", use_container_width=True)

                    if save_btn:
                        payload = {"question_text": e_q, "static_answer": e_a, "category": e_cat}
                        try:
                            put_res = requests.put(f"{API_URL}/api/m18/faqs/{faq_id}", json=payload)
                            if put_res.status_code == 200:
                                st.session_state.faq_editing_id = None
                                st.toast(f"Updated {faq_id}")
                                st.rerun()
                            else:
                                st.error("Failed to update FAQ.")
                        except Exception as e:
                            st.error(f"Error: {e}")
                    if cancel_btn:
                        st.session_state.faq_editing_id = None
                        st.rerun()

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
