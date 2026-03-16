# Module C18 — Clinical Question-Answering System
## Team Guide

> This guide helps any new team member understand the architecture, how the system answers questions, and how to extend it.

---

## 📁 Project Structure

```
module-18/
├── run.py                  # Single entry point — starts both backend & frontend
├── requirements.txt        # Python dependencies
├── .env                    # MongoDB connection string (not committed to git)
├── database/
│   ├── __init__.py
│   └── database.py         # MongoDB schema validators, indexes & seed data
├── backend/
│   ├── __init__.py
│   └── backend.py          # FastAPI REST API (all endpoints)
└── frontend/
    └── frontend.py         # Streamlit UI (Chatbot, Dashboard, FAQ CRUD, Templates)
```

---

## 🏗️ Architecture (3-Tier)

```
┌─────────────┐       ┌──────────────┐       ┌───────────────────┐
│  Streamlit   │──────>│   FastAPI     │──────>│   MongoDB Atlas   │
│  (Frontend)  │<──────│   (Backend)   │<──────│   (Database)      │
│  Port 8501   │  HTTP │   Port 8000   │ PyMongo│  module_18_db     │
└─────────────┘       └──────────────┘       └───────────────────┘
```

---

## 🗃️ Database Collections (ER Diagram)

| Collection            | Purpose                                              | Key Fields                                           |
|----------------------|------------------------------------------------------|------------------------------------------------------|
| `faq_repository`     | Static FAQ pairs (question + pre-written answer)     | `faq_id` (PK), `question_text`, `static_answer`, `category`, `template_id` (FK) |
| `question_templates` | Intent patterns with regex for routing questions     | `intent`, `pattern`, `question_type`, `data_source_required`, `answer_id` (FK→answer_templates) |
| `answer_templates`   | Format rules for rendering answers                   | `answer_id` (PK), `format_type` (Text/Table/Summary), `display_configuration` |
| `evidence_logs`      | Audit trail of every query processed                 | `evidence_id`, `source_reference`, `confidence_score`, `timestamp`, `match_type` |

### Foreign Key Relationships
- `question_templates.answer_id` → `answer_templates.answer_id` (determines how the answer is rendered)
- `faq_repository.template_id` → `question_templates` (links FAQs to intent categories)

---

## 🧠 How Does the System Answer Questions? (DFD Flow)

The system follows a **3-step process** defined in the Level-1 Data Flow Diagram:

### Process 1.0 — Parse Question & Check FAQ
- Uses MongoDB **`$text` search** on `faq_repository`.
- If a match is found → returns the `static_answer` directly.
- **Confidence: 98%** (exact FAQ match).

### Process 2.0 — Match Intent via Templates
- If no FAQ matches, the system loops through `question_templates`.
- Each template has a **regex pattern** (e.g., `patient.*?history`).
- If the user's query matches a regex → the intent is identified (e.g., `patient_history`).
- The system then makes a **mock call to Module 17** to simulate fetching clinical data.
- **Confidence: 85%** (intent-based match).

### Process 3.0 — Format Answer (Dynamic DB Lookup)
- Extracts the `answer_id` FK from the matched template.
- Queries `answer_templates` to get `format_type` (Text, Table, or Summary).
- Formats the answer accordingly for the frontend to render.

### Fallback
- If neither FAQ nor intent matches → returns a polite message asking for a proper clinical query.
- **Confidence: 0%**.

### ⚠️ Important Limitation
The system **cannot answer arbitrary questions**. It can only answer:
1. Questions that match an FAQ via text search (keyword similarity).
2. Questions that match an intent template via regex patterns.

It is **NOT an AI/LLM chatbot** — it is a **database-driven rule-based QA system** designed for a clinical environment. This is correct per the project specification (Module 18 of the DBMS project).

---

## 🔌 API Endpoints

| Method | Endpoint                       | Purpose                                              |
|--------|-------------------------------|------------------------------------------------------|
| POST   | `/api/m18/ask`                | Main QA endpoint — processes user questions          |
| GET    | `/api/m18/faqs`               | List all FAQs                                        |
| POST   | `/api/m18/faqs`               | Create a new FAQ                                     |
| PUT    | `/api/m18/faqs/{faq_id}`      | Update an existing FAQ                               |
| DELETE | `/api/m18/faqs/{faq_id}`      | Delete an FAQ                                        |
| GET    | `/api/m18/hospital/stats`     | Mock hospital statistics for dashboard               |
| GET    | `/api/m18/templates`          | List question intent templates                       |
| GET    | `/api/m18/answer_templates`   | List answer format configurations                    |
| GET    | `/api/m18/analytics/usage`    | Aggregation pipeline: usage stats from evidence_logs |
| GET    | `/api/m18/faqs/stats`         | FAQ count grouped by category                        |

---

## 🚀 How to Run (Step-by-Step)

### Prerequisites
- **Python 3.10+** installed on your system
- **MongoDB Atlas** account with a cluster (free M0 tier works)
- **Internet access** (required to connect to MongoDB Atlas)

### Step 1: Navigate to the Module Directory
```bash
cd DBMS_Project/src/modules/module-18
```

### Step 2: Create & Activate Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate          # Windows
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```
This installs: `fastapi`, `uvicorn`, `pymongo`, `streamlit`, `requests`, `pydantic`, `python-dotenv`

### Step 4: Configure MongoDB Connection
Create a `.env` file in the `module-18/` directory:
```bash
echo 'MONGO_URI="mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?appName=questionansweringsystemforhospital"' > .env
```
> ⚠️ **Important:** URL-encode special characters in the password. For example, `@` becomes `%40`, `#` becomes `%23`.

### Step 5: Run the Application
```bash
python3 run.py
```
This **single command** does everything:
1. Starts the **FastAPI backend** on `http://localhost:8000`
2. Starts the **Streamlit frontend** on `http://localhost:8501`
3. On first run, `setup_database()` auto-creates all 4 collections, applies schema validators, builds text indexes, and seeds initial data (7 FAQs + 5 intent templates + 3 answer templates)

### Step 6: Open in Your Browser

| What | URL |
|------|-----|
| **Frontend (Main App)** | http://localhost:8501 |
| **Swagger API Docs** | http://localhost:8000/docs |
| **ReDoc API Docs** | http://localhost:8000/redoc |

### Step 7: (Optional) Seed 150 FAQs for Testing
```bash
source venv/bin/activate
python3 seed_faqs.py
```

### Step 8: Stop the Application
Press `Ctrl+C` in the terminal. Both servers shut down gracefully.

### Common Issues

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | Make sure the virtual environment is activated: `source venv/bin/activate` |
| `Port 8000 already in use` | Kill the existing process: `lsof -ti:8000 \| xargs kill -9` |
| `Port 8501 already in use` | Kill the existing process: `lsof -ti:8501 \| xargs kill -9` |
| `ServerSelectionTimeoutError` | Check your MongoDB Atlas URI in `.env` and ensure your IP is whitelisted in Atlas |
| `"Database setup complete"` not appearing | Ensure `MONGO_URI` in `.env` is correct and Atlas cluster is running |

### Quick Test Commands
After the application is running, you can test the backend directly:
```bash
# Test the main QA endpoint
curl -X POST http://localhost:8000/api/m18/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the standard dosage for Aspirin?"}'

# List all FAQs
curl http://localhost:8000/api/m18/faqs

# Check intent templates
curl http://localhost:8000/api/m18/templates

# Check hospital stats (dashboard data)
curl http://localhost:8000/api/m18/hospital/stats
```

---

## 🔧 How to Extend

### Adding a new FAQ
Use the "📝 Manage FAQs" tab in the UI, or POST to `/api/m18/faqs`.

### Adding a new intent (question type)
1. Add a new entry in `_default_templates` inside `database/database.py`.
2. Set the `pattern` regex, `data_source_required`, and link an `answer_id`.
3. Add a corresponding mock data branch in `backend.py` under the Module 17 mock section.
4. Run `setup_database()` to upsert the new template.

### Adding a new answer format
1. Insert a new document into `answer_templates` with a new `format_type`.
2. Update `frontend.py` to handle the new format in the chatbot rendering logic.

---

## 📊 Advanced DBMS Feature: Aggregation Pipelines

The `GET /api/m18/analytics/usage` endpoint demonstrates MongoDB's aggregation framework:

```javascript
[
  { $group: { _id: "$match_type", count: { $sum: 1 }, avg_confidence: { $avg: "$confidence_score" } } },
  { $sort: { count: -1 } }
]
```

This groups all evidence logs by how the query was matched (exact FAQ, intent, or none), counts the frequency, and calculates average confidence. Results are displayed as metrics and a bar chart in the Dashboard tab.

---

## 👥 Team

- **Module 18** is isolated from other modules by design.
- We mock data from "Module 17 (Smart Clinical Views)" since we cannot directly query their database.
- All query processing is logged to `evidence_logs`, simulating integration with "Module 49 (Integrated CDS)".
