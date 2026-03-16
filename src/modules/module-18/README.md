# Module C18: Clinical Question-Answering System

**Project:** AI-Based Clinical Decision Support System  
**Course:** DBMS Mini Project  
**Tech Stack:** Streamlit (Frontend), FastAPI (Backend), MongoDB Atlas (Database)

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
* *See `backend.py`: The `mock_module_17_response` variable generates fake clinical data so the UI can be tested independently.*

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
