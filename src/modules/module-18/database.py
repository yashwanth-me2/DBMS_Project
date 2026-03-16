import os
from pymongo import MongoClient

import urllib.parse
# Use the parsed credentials to form the correct MongoDB connection string
MONGO_URI = os.getenv("MONGO_URI", f"mongoose")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Check if we can connect
    client.server_info()
    print("Connected to MongoDB successfully!")
except Exception as e:
    print(f"Warning: Could not connect to MongoDB. Ensure your MONGO_URI is correct. Error: {e}")
    client = MongoClient("mongodb://localhost:27017") # Fallback to local
    
# Module 18 Database
db = client['module_18_db']

# Collections based on ER diagram
faq_repository = db['faq_repository']
question_templates = db['question_templates']
evidence_logs = db['evidence_logs']

def init_db():
    """Initialize the database with some dummy FAQ and Template data."""
    try:
        # Insert dummy FAQs if empty
        if faq_repository.count_documents({}) == 0:
            faq_repository.insert_many([
                {
                    "faq_id": "F001", 
                    "question_text": "What are the common side effects of lisinopril?", 
                    "static_answer": "Common side effects of lisinopril include cough, dizziness, headache, and hyperkalemia.", 
                    "category": "Medication"
                },
                {
                    "faq_id": "F002", 
                    "question_text": "What is the normal range for fasting blood glucose?", 
                    "static_answer": "A normal fasting blood glucose level is generally between 70 and 99 mg/dL.", 
                    "category": "Lab Values"
                }
            ])
            print("Inserted dummy FAQ data.")
        
        # Insert dummy templates if empty
        if question_templates.count_documents({}) == 0:
            question_templates.insert_many([
                {
                    "template_id": "T001", 
                    "query_type": "patient_history", 
                    "pattern_text": "patient.*history|history.*patient|past medical history"
                },
                {
                    "template_id": "T002", 
                    "query_type": "medication_guidance", 
                    "pattern_text": "medication|dosage|side effect|prescribe"
                },
            ])
            print("Inserted dummy question template data.")
            
    except Exception as e:
        print(f"Failed to initialize database: {e}")

if __name__ == "__main__":
    init_db()
