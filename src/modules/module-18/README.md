# Module C18: Clinical Question-Answering System

**Project:** AI-Based Clinical Decision Support System  
**Course:** DBMS Mini Project  
**Tech Stack:** Streamlit (Frontend), FastAPI (Backend), MongoDB Atlas (Database)

---

## 🏗️ Project Structure

```
module-18/
├── .env                          # MongoDB Atlas connection string
├── app.py                        # Entry point — starts both backend & frontend
├── start.sh                      # Shell script to start both servers
├── requirements.txt              # Python dependencies
├── seed_faqs.py                  # Bulk-insert 150+ FAQs
├── vercel.json                   # Deployment config
│
├── backend/
│   ├── __init__.py
│   └── backend.py                # FastAPI app — all API routes & QA pipeline
│ 
├── frontend/
│   ├── __init__.py
│   └── frontend.py               # Streamlit UI — Chatbot, Dashboard, FAQs, Templates, API
│
└── database/
    ├── __init__.py
    └── database.py               # MongoDB connection, schema validation, indexes, seeding
```

---

## 🔄 Chatbot Flow — What Happens When You Ask a Question

When a user types a query in the **💬 Chatbot** tab and presses Enter, the following pipeline executes:

### Step 1 · User Input Captured

The Streamlit frontend captures the query string and sends an HTTP `POST` request to the FastAPI backend at `/api/m18/ask`.

### Step 2 · Process 1.0 — FAQ Repository Search (MongoDB `$text` Index)
The backend performs a **full-text search** on the `faq_repository` collection using MongoDB's `$text` operator. Results are sorted by `textScore` (relevance).

```python
results = faq_repository.find(
    {"$text": {"$search": user_query}},
    {"score": {"$meta": "textScore"}, "faq_id": 1, "question_text": 1, ...}
).sort([("score", {"$meta": "textScore"})]).limit(3)
```

### Step 3 · Strict Validation — Keyword Overlap Check
If the best FAQ score ≥ **3.0** (threshold), the system extracts keywords from both the user query and the FAQ question, then checks if ≥ **50%** of user keywords appear in the FAQ. This prevents false-positive matches.

```python
user_keywords = _extract_keywords(query)        # removes stop-words
hits, ratio = _keyword_overlap_score(user_keywords, faq["question_text"])
if ratio >= 0.50:   # Accept match
    return faq["static_answer"]
```

### Step 4 · Fallback — Regex Keyword Search
If no FAQ passes the `$text` + overlap check, the system tries a **regex-based keyword search** on `question_text` with the same overlap validation.

```python
regex_pattern = "|".join(re.escape(k) for k in user_keywords)
candidates = faq_repository.find(
    {"question_text": {"$regex": regex_pattern, "$options": "i"}}
)
```

### Step 5 · Process 2.0 — Intent Template Matching
If no FAQ matches at all, the system iterates through `question_templates` and matches the query against each template's **regex pattern**.

```python
for template in question_templates.find({}):
    if re.search(template["pattern"], query, re.IGNORECASE):
        intent = template["intent"]  # e.g., "medication_guidance"
        data_source = template["data_source_required"]  # e.g., "Pharmacy_DB"
        break
```

### Step 6 · Module 17 Data Fetch (Cross-Module Integration)
Once an intent is matched, the backend calls **Module 17 (Smart Clinical Views)** to fetch real clinical data. If Module 17 is unavailable, structured **mock data** is returned as a fallback.

```python
def fetch_module_17_data(intent_type, parsed_entities):
    try:
        resp = requests.get("http://module17-api:8080/data",
                            params={"intent": intent_type}, timeout=2)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException:
        return get_mock_data(intent_type)  # Structured mock fallback
```

### Step 7 · Process 3.0 — Answer Template FK Lookup
The system follows a **foreign key chain** to determine how to format the answer:
`FAQ.template_id` → `question_templates.intent` → `answer_id` → `answer_templates.format_type`
Possible formats: **Text**, **Table**, **Chart**, **Summary**

```python
qt_doc = question_templates.find_one({"intent": faq["template_id"]})
ans_doc = answer_templates.find_one({"answer_id": qt_doc["answer_id"]})
format_type = ans_doc["format_type"]  # "Text" | "Table" | "Chart" | "Summary"
```

### Step 8 · Evidence Logging (Audit Trail)
Every query is logged to the `evidence_logs` collection with a unique ID, match type, confidence score, and timestamp.

### Step 9 · Module 49 Silent Background Log (Async)
An async background task sends the log data to Module 49 (Integrated CDS). This **never blocks** the user response and output goes **only** to the server terminal.

```python
asyncio.ensure_future(send_log_to_module_49(log_entry))
```

### Step 10 · Response Rendered in Frontend
The Streamlit frontend receives the JSON response and renders it based on `format_type`:
- **Text** → `st.markdown(answer)`
- **Table** → `st.dataframe(pd.DataFrame(answer))`
- **Chart** → `st.bar_chart(data)`
- **Summary** → `st.info(answer)`

*If no FAQ or intent template matches, the system returns a fallback message asking the user to rephrase their clinical query.*

---

## 🏗️ Architecture & Project Rules
This module strictly adheres to the architectural guidelines of the DBMS Clinical Decision Support System:
1. **Isolation Principle:** This module cannot directly query external clinical databases (like Pharmacy or Lab). All dynamic patient data requests are routed through Module 17.
2. **Three-Tier Architecture:** The system is separated into a user interface (`frontend.py`), a routing and logic engine (`backend.py`), and a database connection/initialization script (`database.py`).
3. **Database-Driven Logic:** System routing is determined by querying the database for FAQs and intent templates, rather than using hardcoded nested `if/else` statements.

---

## 🔗 The Module 17 Integration (Mock vs. Future)

Because this is a distributed system, Module 18 acts as the "brain" that parses questions, but it does not store patient medical records. 

### Current State (Mock Data)
Since Module 17 (Smart Clinical Views) is being developed by another team, our backend currently uses **Mock Data**. When a doctor asks for patient history, our backend simulates an API response from Module 17. 
* *See `backend.py`: The `fetch_module_17_data` function generates structured clinical data so the UI can be tested independently.*

### Future State (Real Integration)
Once the Module 17 team provides their API endpoint, we will replace the mock variable with an actual HTTP request using the `requests` library. 

```python
# Future integration code for backend.py
import requests

module_17_url = "http://module17-api.com/api/get_view"
response = requests.get(module_17_url, params={"query_type": query_type})
real_clinical_data = response.json()
```

---

## 🚀 How to Run Locally

### 1. Environment Setup
Create a Python virtual environment and install the required dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Database Connection
Set your MongoDB Atlas connection string as an environment variable (or let the system fallback to local testing):
```bash
export MONGO_URI="mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority"
```

Initialize the database schemas and sample data:
```bash
python database.py
```

### 3. Start the Backend
Start the FastAPI server (it runs on port 8000 by default):
```bash
uvicorn backend:app --reload --host 0.0.0.0 --port 8000
```

### 4. Start the Frontend
In a new terminal (with the virtual environment activated), start the Streamlit UI:
```bash
streamlit run frontend.py
```

Open the provided `localhost` link in your browser to interact with the Clinical Question-Answering System!
