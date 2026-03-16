import os
import re
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from database.database import (
    faq_repository,
    question_templates,
    evidence_logs,
    answer_templates,
    setup_database,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run DB setup once when the server starts."""
    try:
        setup_database()
    except Exception as e:
        print(f"WARNING: DB setup failed at startup: {e}")
    yield


app = FastAPI(title="Clinical Query Copilot API", lifespan=lifespan)


class QueryRequest(BaseModel):
    query: str

class FAQCreate(BaseModel):
    faq_id: str
    question_text: str
    static_answer: str
    category: str

class FAQUpdate(BaseModel):
    question_text: str | None = None
    static_answer: str | None = None
    category: str | None = None


# ── GET /api/m18/faqs/stats ────────────────────────────────────────────────
@app.get("/api/m18/faqs/stats")
async def get_faq_stats():
    try:
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}}
        ]
        result = list(faq_repository.aggregate(pipeline))
        stats = {item["_id"]: item["count"] for item in result}
        return {"status": "success", "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── GET /api/m18/hospital/stats ───────────────────────────────────────────
@app.get("/api/m18/hospital/stats")
async def get_hospital_stats():
    # Return mock hospital statistics for the dashboard
    return {
        "status": "success",
        "data": {
            "Total Doctors": 145,
            "Active Wards": 22,
            "Total Beds": 500,
            "Available Beds": 42,
            "Specialized Facilities": ["ICU", "NICU", "Cardiology", "Neurology", "Oncology"]
        }
    }

# ── GET /api/m18/templates ────────────────────────────────────────────────
@app.get("/api/m18/templates")
async def get_templates():
    try:
        templates = list(question_templates.find({}, {"_id": 0}))
        return {"status": "success", "data": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── GET /api/m18/answer_templates ─────────────────────────────────────────
@app.get("/api/m18/answer_templates")
async def get_answer_templates():
    try:
        templates = list(answer_templates.find({}, {"_id": 0}))
        return {"status": "success", "data": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── FAQ CRUD ENDPOINTS ────────────────────────────────────────────────────
@app.get("/api/m18/faqs")
async def get_faqs():
    try:
        faqs = list(faq_repository.find({}, {"_id": 0}))
        return {"status": "success", "data": faqs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/m18/faqs")
async def create_faq(faq: FAQCreate):
    try:
        if faq_repository.find_one({"faq_id": faq.faq_id}):
            raise HTTPException(status_code=400, detail="FAQ ID already exists.")
        faq_repository.insert_one(faq.dict())
        return {"status": "success", "message": "FAQ created successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/m18/faqs/{faq_id}")
async def update_faq(faq_id: str, faq_update: FAQUpdate):
    try:
        update_data = {k: v for k, v in faq_update.dict().items() if v is not None}
        if not update_data:
            return {"status": "success", "message": "No changes provided."}
        result = faq_repository.update_one({"faq_id": faq_id}, {"$set": update_data})
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="FAQ not found.")
        return {"status": "success", "message": "FAQ updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/m18/faqs/{faq_id}")
async def delete_faq(faq_id: str):
    try:
        result = faq_repository.delete_one({"faq_id": faq_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="FAQ not found.")
        return {"status": "success", "message": "FAQ deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── POST /api/m18/ask ─────────────────────────────────────────────────────
@app.post("/api/m18/ask")
async def ask_question(request: QueryRequest):
    query = request.query
    from typing import Any
    log_entry: dict[str, Any] = {
        "log_id": str(uuid.uuid4()),
        "query": query,
        "timestamp": datetime.utcnow(),
    }

    try:
        # ---- Process 1.0: Parse Question & Check FAQ ----
        search_results = list(
            faq_repository.find(
                {"$text": {"$search": query}},
                {
                    "score": {"$meta": "textScore"},
                    "faq_id": 1,
                    "question_text": 1,
                    "static_answer": 1,
                    "category": 1,
                    "template_id": 1,
                },
            ).sort([("score", {"$meta": "textScore"})]).limit(1)
        )

        if search_results:
            match = search_results[0]
            
            # Formulate mock evidence
            log_entry["match_type"] = "exact"
            log_entry["evidence_id"] = f"ev_{uuid.uuid4().hex[:8]}"
            log_entry["source_reference"] = "FAQ Repository"
            log_entry["confidence_score"] = 0.98
            evidence_logs.insert_one(log_entry)
            
            # Process 3.0: Format Answer (Fetch Text format)
            ans_template = answer_templates.find_one({"format_type": "Text"})
            if isinstance(ans_template, dict):
                format_type = ans_template.get("format_type", "Text")
            else:
                format_type = "Text"

            # Log Usage (Module 49)
            print(f"[Module 49: Integrated CDS] Usage logged. Query: '{query}' -> FAQ Match")

            return {
                "answer": match.get("static_answer", "Answer not found."),
                "confidence_score": 0.98,
                "citation": f"FAQ Database – {match.get('category', 'General')}",
                "format_type": format_type,
                "timestamp": log_entry["timestamp"].isoformat() + "Z"
            }

        # ---- Process 2.0: Match and Retrieve Data ----
        templates = list(question_templates.find({}))
        for template in templates:
            pattern = template.get("pattern", "")
            if pattern and re.search(pattern, query, re.IGNORECASE):
                intent = template.get("intent", "unknown")
                question_type = template.get("question_type", "Factual")
                data_source_required = template.get("data_source_required", "Unknown_DB")
                
                # ---- Mock Module 17 Call ----
                # Simulating "Aggregated Clinical Data" from Module 17 based on data_source_required
                format_type_to_request = "Text"
                if data_source_required == "Patient_Records_DB":
                    mock_answer = "[Mocked Data from Module 17 - Smart Clinical Views] The patient is a 45-year-old male with a history of Type 2 Diabetes Mellitus and Hypertension. His last HbA1c was 7.2%. No known drug allergies."
                elif data_source_required == "Pharmacy_DB":
                    mock_answer = "[Mocked Data from Module 17 - Smart Clinical Views] Common side effects for Metformin include gastrointestinal upset, nausea, and diarrhea. Recommend taking with meals to minimize discomfort."
                elif data_source_required == "Hospital_Analytics_DB":
                    # Statistical data usually implies a Table formatting requirement
                    format_type_to_request = "Table"
                    mock_answer = [
                        {"Symptom": "Fever", "Count": 142, "Avg_Recovery_Days": 3.2},
                        {"Symptom": "Cough", "Count": 89, "Avg_Recovery_Days": 5.1},
                        {"Symptom": "Fatigue", "Count": 210, "Avg_Recovery_Days": 7.5}
                    ]
                elif data_source_required == "Hospital_Overview_DB":
                    format_type_to_request = "Table"
                    mock_answer = [
                        {"Metric": "Total Doctors", "Value": 145},
                        {"Metric": "Active Wards", "Value": 22},
                        {"Metric": "Total Beds", "Value": 500},
                        {"Metric": "Available Beds", "Value": 42},
                        {"Metric": "Specialized Facilities", "Value": "ICU, NICU, Cardiology, Neurology, Oncology"}
                    ]
                else:
                    mock_answer = f"[Mocked Data from Module 17 - Smart Clinical Views] Generic result for intent: {intent}"

                # ---- Fetch Evidence ----
                log_entry["match_type"] = "intent"
                log_entry["evidence_id"] = f"ev_{uuid.uuid4().hex[:8]}"
                log_entry["source_reference"] = f"Module 17 ({data_source_required})"
                log_entry["confidence_score"] = 0.85
                evidence_logs.insert_one(log_entry)

                # ---- Process 3.0: Format Answer ----
                ans_template = answer_templates.find_one({"format_type": format_type_to_request})
                if isinstance(ans_template, dict):
                    chosen_format = ans_template.get("format_type", "Text")
                else:
                    chosen_format = "Text"

                # ---- Log Usage (Module 49) ----
                print(f"[Module 49: Integrated CDS] Usage logged. Query: '{query}' -> Intent: {intent}")

                return {
                    "answer": mock_answer,
                    "confidence_score": 0.85,
                    "citation": f"Intent Match: {intent} ({question_type})",
                    "format_type": chosen_format,
                    "timestamp": log_entry["timestamp"].isoformat() + "Z"
                }

        # Fallback (for non-medical or unparseable queries)
        log_entry["match_type"] = "none"
        log_entry["evidence_id"] = f"ev_{uuid.uuid4().hex[:8]}"
        log_entry["source_reference"] = "None"
        log_entry["confidence_score"] = 0.0
        evidence_logs.insert_one(log_entry)
        
        print(f"[Module 49: Integrated CDS] Usage logged. Query: '{query}' -> No Match")

        return {
            "answer": (
                "⚠️ I am a Clinical Assistant. Your query doesn't match our clinical records or intent templates. "
                "Please enter a proper medical query, such as 'What is the standard dosage for Aspirin?' "
                "or 'Show patient history'."
            ),
            "confidence_score": 0.0,
            "citation": "None (Unrecognized Query)",
            "format_type": "Text",
            "timestamp": log_entry["timestamp"].isoformat() + "Z"
        }

    except Exception as e:
        log_entry["error"] = str(e)
        evidence_logs.insert_one(log_entry)
        raise HTTPException(status_code=500, detail=str(e))
