import os
import re
from pathlib import Path
from urllib.parse import urlparse, quote_plus, unquote
from pymongo import MongoClient, TEXT
from pymongo.errors import CollectionInvalid
from dotenv import load_dotenv

# Load .env from the module-18 root (works whether run from backend/ or module-18/)
_env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=_env_path)

# Streamlit Cloud uses st.secrets instead of .env files
# Check st.secrets first, then fall back to environment variables
def _get_mongo_uri():
    try:
        import streamlit as st
        if "MONGO_URI" in st.secrets:
            return st.secrets["MONGO_URI"]
    except Exception:
        pass
    return os.getenv("MONGO_URI", "mongodb://localhost:27017")

def _fix_mongo_uri(uri):
    """Re-encode credentials with quote_plus for newer pymongo (RFC 3986)."""
    try:
        parsed = urlparse(uri)
        if not parsed.username:
            return uri
        username = quote_plus(unquote(parsed.username))
        password = quote_plus(unquote(parsed.password)) if parsed.password else ""
        host = parsed.hostname
        if parsed.port:
            host += f":{parsed.port}"
        netloc = f"{username}:{password}@{host}" if password else f"{username}@{host}"
        fixed = f"{parsed.scheme}://{netloc}{parsed.path}"
        if parsed.query:
            fixed += f"?{parsed.query}"
        if parsed.fragment:
            fixed += f"#{parsed.fragment}"
        return fixed
    except Exception:
        return uri

MONGO_URI = _fix_mongo_uri(_get_mongo_uri())

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
db = client.module_18_db


# These will be populated by setup_database()
faq_repository = db.faq_repository
question_templates = db.question_templates
evidence_logs = db.evidence_logs
answer_templates = db.answer_templates  # NEW collection


def setup_database():
    """Apply schema validation, create indexes, and seed initial data."""
    
    # 1. FAQ Repository Validator
    faq_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["faq_id", "question_text", "static_answer", "category", "template_id"],
            "properties": {
                "faq_id":         {"bsonType": "string"},
                "question_text":  {"bsonType": "string"},
                "static_answer":  {"bsonType": "string"},
                "category":       {"enum": ["Medication", "Lab Values", "General", "Procedure"]},
                "template_id":    {"bsonType": "string"} # FK to Question Templates
            }
        }
    }

    try:
        db.create_collection("faq_repository", validator=faq_validator)
    except CollectionInvalid:
        db.command("collMod", "faq_repository", validator=faq_validator)
        
    faq_repository.create_index([("question_text", TEXT)], default_language="english")

    if faq_repository.count_documents({}) == 0:
        faq_repository.insert_many([
            {
                "faq_id": "faq_001",
                "question_text": "What is the standard dosage for Aspirin?",
                "static_answer": "The standard dose is 81 mg to 325 mg once daily.",
                "category": "Medication",
                "template_id": "qt_med_01"
            },
            {
                "faq_id": "faq_002",
                "question_text": "What is the normal range for fasting blood sugar?",
                "static_answer": (
                    "A fasting blood sugar level from 70 to 99 mg/dL "
                    "(3.9 to 5.5 mmol/L) is considered normal."
                ),
                "category": "Lab Values",
                "template_id": "qt_lab_01"
            },
            {
                "faq_id": "faq_003",
                "question_text": "What are the common side effects of Lisinopril?",
                "static_answer": "Common side effects include a dry, persistent cough, dizziness, and headaches.",
                "category": "Medication",
                "template_id": "qt_med_02"
            },
            {
                "faq_id": "faq_004",
                "question_text": "How do I prepare for an MRI scan?",
                "static_answer": "You should leave all metallic objects at home. Wear comfortable, loose-fitting clothing without metal fasteners. Follow any specific fasting instructions given by your doctor.",
                "category": "General",
                "template_id": "qt_gen_01"
            },
            {
                "faq_id": "faq_005",
                "question_text": "What is a normal resting heart rate for adults?",
                "static_answer": "A normal resting heart rate for most adults ranges from 60 to 100 beats per minute.",
                "category": "Lab Values",
                "template_id": "qt_lab_02"
            },
            {
                "faq_id": "faq_006",
                "question_text": "What should I bring to my first appointment?",
                "static_answer": "Please bring your photo ID, insurance card, a list of current medications, and any previous medical records or test results.",
                "category": "General",
                "template_id": "qt_gen_02"
            },
            {
                "faq_id": "faq_007",
                "question_text": "When should I take Atorvastatin?",
                "static_answer": "It is generally recommended to take Atorvastatin once a day at the same time every day. Many doctors suggest taking it in the evening.",
                "category": "Medication",
                "template_id": "qt_med_03"
            }
        ])

    # 2. Question Templates Validator & Seeding
    # Add: query_log_id, question_type, data_source_required
    _default_templates = [
        {
            "intent": "patient_history",
            "pattern": r"patient.*?history|history.*?patient|past.*?record|medical.*?record|last\s+\d+\s+days|recent.*?visit|previous.*?diagnosis|admission.*?history",
            "query_log_id": "log_tmpl_01",
            "question_type": "Temporal",
            "data_source_required": "Patient_Records_DB",
            "answer_id": "ans_tmpl_text"
        },
        {
            "intent": "medication_guidance",
            "pattern": r"medication|dosage|side\s*effects?|drug.*?interact|prescri(?:be|ption)|administer|contraindication|dose\b|pharma",
            "query_log_id": "log_tmpl_02",
            "question_type": "Factual",
            "data_source_required": "Pharmacy_DB",
            "answer_id": "ans_tmpl_text"
        },
        {
            "intent": "statistical_query",
            "pattern": r"statistic|trend|symptom.*?count|avg|average.*?recovery|outbreak|frequency",
            "query_log_id": "log_tmpl_03",
            "question_type": "Statistical",
            "data_source_required": "Hospital_Analytics_DB",
            "answer_id": "ans_tmpl_table"
        },
        {
            "intent": "dashboard_stats",
            "pattern": r"number.*?patients|how many.*?doctors|active.*?wards|hospital.*?stats|available.*?beds|total.*?beds|hospital.*?overview|capacity",
            "query_log_id": "log_tmpl_04",
            "question_type": "Statistical",
            "data_source_required": "Hospital_Overview_DB",
            "answer_id": "ans_tmpl_table"
        },
        {
            "intent": "comparative_analysis",
            "pattern": r"compare|difference\s+between|versus|vs\b|better",
            "query_log_id": "log_tmpl_05",
            "question_type": "Comparative",
            "data_source_required": "Hospital_Analytics_DB",
            "answer_id": "ans_tmpl_table"
        },
    ]
    for t in _default_templates:
        question_templates.update_one(
            {"intent": t["intent"]},
            {"$set": t},
            upsert=True,
        )


    # 3. Answer Templates Validator & Seeding
    # Fields: answer_id (PK), display_configuration, format_type
    answer_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["answer_id", "display_configuration", "format_type"],
            "properties": {
                "answer_id":             {"bsonType": "string"},
                "display_configuration": {"bsonType": "string"},
                "format_type":           {"enum": ["Text", "Table", "Chart", "Summary"]}
            }
        }
    }
    try:
        db.create_collection("answer_templates", validator=answer_validator)
    except CollectionInvalid:
        db.command("collMod", "answer_templates", validator=answer_validator)

    if answer_templates.count_documents({}) == 0:
        answer_templates.insert_many([
            {
                "answer_id": "ans_tmpl_text",
                "display_configuration": "Standard markdown rendering",
                "format_type": "Text"
            },
            {
                "answer_id": "ans_tmpl_table",
                "display_configuration": "Render as structured data grid",
                "format_type": "Table"
            },
            {
                "answer_id": "ans_tmpl_summary",
                "display_configuration": "Bullet point highlighted summary",
                "format_type": "Summary"
            },
            {
                "answer_id": "ans_tmpl_chart",
                "display_configuration": "Render as bar chart visualisation",
                "format_type": "Chart"
            }
        ])

    # 4. Evidence Logs Validator
    # Fields: evidence_id, source_reference, confidence_score, timestamp
    evidence_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["evidence_id", "source_reference", "confidence_score", "timestamp"],
            "properties": {
                "evidence_id":      {"bsonType": "string"},
                "source_reference": {"bsonType": "string"},
                "confidence_score": {"bsonType": "double"},
                "timestamp":        {"bsonType": "date"}
            }
        }
    }


    try:
        db.create_collection("evidence_logs", validator=evidence_validator)
    except CollectionInvalid:
        db.command("collMod", "evidence_logs", validator=evidence_validator)

    print("Database setup complete.")


if __name__ == "__main__":
    setup_database()
    print("faq_repository:", faq_repository.name)
    print("question_templates:", question_templates.name)
