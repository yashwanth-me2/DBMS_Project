import asyncio
import json
import os
import re
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

import requests as http_requests  # stdlib-safe HTTP client for Module 17
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


# ═══════════════════════════════════════════════════════════════════════════
# MODULE 49 — SILENT BACKGROUND LOGGER  (Task 4)
# Runs on EVERY query; output goes ONLY to the server terminal, NEVER to
# the frontend response.
# ═══════════════════════════════════════════════════════════════════════════
async def send_log_to_module_49(log_data: dict) -> None:
    """Simulate an async POST to Module 49 (Integrated CDS Usage Logger).
    This runs in the background and NEVER adds data to the API response."""
    try:
        await asyncio.sleep(0)  # Yield to event-loop (non-blocking)
        sanitized = {
            "log_id": log_data.get("log_id"),
            "query": log_data.get("query"),
            "match_type": log_data.get("match_type", "none"),
            "confidence_score": log_data.get("confidence_score", 0.0),
            "source_reference": log_data.get("source_reference", "N/A"),
            "timestamp": str(log_data.get("timestamp", "")),
        }
        print(
            f"[Module 49 → POST /api/m49/usage-log]  "
            f"Payload: {json.dumps(sanitized, indent=None)}"
        )
    except Exception as exc:
        print(f"[Module 49] Silent log failed (non-critical): {exc}")


# ═══════════════════════════════════════════════════════════════════════════
# MODULE 17 — REALISTIC API CALL + MOCK FALLBACK  (Task 3)
# ═══════════════════════════════════════════════════════════════════════════
MODULE_17_URL = os.getenv("MODULE_17_URL", "http://module17-api:8080/data")


def fetch_module_17_data(intent_type: str, parsed_entities: dict):
    """Attempt a real GET to Module 17. On failure, return structured mock data.

    Parameters
    ----------
    intent_type : str
        The matched intent (e.g. 'comparative_analysis', 'statistical_query').
    parsed_entities : dict
        Contextual info extracted from the query (data_source, keywords, etc.).
    """
    # --- 1. Attempt real HTTP call to Module 17 ---
    try:
        resp = http_requests.get(
            MODULE_17_URL,
            params={"intent": intent_type, "source": parsed_entities.get("data_source", "")},
            timeout=2,
        )
        resp.raise_for_status()
        print(f"[Module 17] Live data received for intent={intent_type}")
        return resp.json()
    except http_requests.exceptions.RequestException as exc:
        print(f"[Module 17] API unreachable ({exc}). Falling back to mock data.")

    # --- 2. Mock fallback (structured per intent) ---
    data_source = parsed_entities.get("data_source", "")

    if intent_type == "comparative_analysis":
        return [
            {"Metric": "Avg Recovery Days", "Aspirin": 4.2, "Ibuprofen": 3.8},
            {"Metric": "Side Effect Rate", "Aspirin": "12%", "Ibuprofen": "18%"},
            {"Metric": "Cost per Dose", "Aspirin": "$0.05", "Ibuprofen": "$0.12"},
            {"Metric": "Patient Satisfaction", "Aspirin": "87%", "Ibuprofen": "82%"},
        ]

    if intent_type == "statistical_query":
        return [
            {"Symptom": "Fever", "Count": 142, "Avg_Recovery_Days": 3.2},
            {"Symptom": "Cough", "Count": 89, "Avg_Recovery_Days": 5.1},
            {"Symptom": "Fatigue", "Count": 210, "Avg_Recovery_Days": 7.5},
        ]

    if intent_type == "dashboard_stats":
        return [
            {"Metric": "Total Doctors", "Value": 145},
            {"Metric": "Active Wards", "Value": 22},
            {"Metric": "Total Beds", "Value": 500},
            {"Metric": "Available Beds", "Value": 42},
            {"Metric": "Specialized Facilities", "Value": "ICU, NICU, Cardiology, Neurology, Oncology"},
        ]

    if data_source == "Patient_Records_DB" or intent_type == "patient_history":
        return (
            "[Mocked Data from Module 17 — Smart Clinical Views] "
            "The patient is a 45-year-old male with a history of Type 2 Diabetes "
            "Mellitus and Hypertension. His last HbA1c was 7.2%. No known drug allergies."
        )

    if data_source == "Pharmacy_DB" or intent_type == "medication_guidance":
        return (
            "[Mocked Data from Module 17 — Smart Clinical Views] "
            "Common side effects for Metformin include gastrointestinal upset, "
            "nausea, and diarrhea. Recommend taking with meals to minimize discomfort."
        )

    # Generic fallback
    return f"[Mocked Data from Module 17 — Smart Clinical Views] Generic result for intent: {intent_type}"


# ═══════════════════════════════════════════════════════════════════════════
# FAQ SCORING HELPERS  (Task 1)
# ═══════════════════════════════════════════════════════════════════════════
_STOP_WORDS = frozenset({
    "the", "what", "how", "who", "is", "are", "was", "for", "and", "this",
    "that", "with", "from", "can", "does", "will", "a", "an", "of", "to",
    "in", "on", "it", "be", "do", "not", "by", "at", "or", "so", "if",
    "my", "me", "we", "you", "your", "our", "they", "them", "its", "has",
    "had", "have", "been", "would", "could", "should", "about", "there",
})

# Minimum MongoDB $text search score to accept an FAQ match
FAQ_TEXT_SCORE_THRESHOLD = 3.0
# Minimum fraction of user keywords that must appear in the FAQ text
FAQ_KEYWORD_OVERLAP_MIN_RATIO = 0.50


def _extract_keywords(text: str) -> list[str]:
    """Return lowercase non-stop-word tokens (len > 2) from *text*."""
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 2 and w not in _STOP_WORDS]


def _keyword_overlap_score(keywords: list[str], faq_text: str) -> tuple[int, float]:
    """Return (matched_count, overlap_ratio) of *keywords* found in *faq_text*."""
    faq_lower = faq_text.lower()
    hits = sum(1 for k in keywords if k in faq_lower)
    ratio = hits / len(keywords) if keywords else 0.0
    return hits, ratio


# ═══════════════════════════════════════════════════════════════════════════
# REQUEST / RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════════════
class QueryRequest(BaseModel):
    query: str


class FAQCreate(BaseModel):
    faq_id: str
    question_text: str
    static_answer: str
    category: str
    template_id: str = "qt_gen_default"


class FAQUpdate(BaseModel):
    question_text: str | None = None
    static_answer: str | None = None
    category: str | None = None


# ═══════════════════════════════════════════════════════════════════════════
# READ-ONLY ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

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


@app.get("/api/m18/hospital/stats")
async def get_hospital_stats():
    return {
        "status": "success",
        "data": {
            "Total Doctors": 145,
            "Active Wards": 22,
            "Total Beds": 500,
            "Available Beds": 42,
            "Specialized Facilities": ["ICU", "NICU", "Cardiology", "Neurology", "Oncology"],
        },
    }


@app.get("/api/m18/templates")
async def get_templates():
    try:
        templates = list(question_templates.find({}, {"_id": 0}))
        return {"status": "success", "data": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/m18/answer_templates")
async def get_answer_templates():
    try:
        templates = list(answer_templates.find({}, {"_id": 0}))
        return {"status": "success", "data": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/m18/analytics/usage")
async def get_usage_analytics():
    """MongoDB Aggregation Pipeline: groups evidence_logs by match_type,
    counts frequency, and calculates average confidence_score."""
    try:
        pipeline = [
            {
                "$group": {
                    "_id": "$match_type",
                    "count": {"$sum": 1},
                    "avg_confidence": {"$avg": "$confidence_score"},
                }
            },
            {"$sort": {"count": -1}},
        ]
        result = list(evidence_logs.aggregate(pipeline))
        data = [
            {
                "match_type": item["_id"] if item["_id"] else "unknown",
                "count": item["count"],
                "avg_confidence": round(item["avg_confidence"], 2) if item["avg_confidence"] else 0.0,
            }
            for item in result
        ]
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# FAQ CRUD
# ═══════════════════════════════════════════════════════════════════════════

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
    except HTTPException:
        raise
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/m18/faqs/{faq_id}")
async def delete_faq(faq_id: str):
    try:
        result = faq_repository.delete_one({"faq_id": faq_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="FAQ not found.")
        return {"status": "success", "message": "FAQ deleted successfully."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# POST /api/m18/ask  —  MAIN QA PIPELINE
# Process 1.0 → FAQ check  (Task 1: strict scoring)
# Process 2.0 → Intent templates + Module 17 data  (Task 3)
# Process 3.0 → Answer formatting via answer_templates FK  (Task 2)
# Background  → Module 49 silent log  (Task 4)
# ═══════════════════════════════════════════════════════════════════════════

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
        # ────────────────────────────────────────────────────────────────
        # PROCESS 1.0 — Parse Question & Check FAQ  (Task 1: strict)
        # ────────────────────────────────────────────────────────────────
        faq_match = None

        # 1a. Try MongoDB $text search with STRICT textScore threshold
        try:
            text_results = list(
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
                )
                .sort([("score", {"$meta": "textScore"})])
                .limit(3)
            )
            if text_results:
                best = text_results[0]
                best_score = best.get("score", 0.0)
                if best_score >= FAQ_TEXT_SCORE_THRESHOLD:
                    # Double-check with keyword overlap to prevent false positives
                    user_kws = _extract_keywords(query)
                    if user_kws:
                        hits, ratio = _keyword_overlap_score(user_kws, best.get("question_text", ""))
                        if ratio >= FAQ_KEYWORD_OVERLAP_MIN_RATIO:
                            faq_match = best
                            print(f"[FAQ] $text match accepted  score={best_score:.2f}  overlap={ratio:.0%}")
                        else:
                            print(f"[FAQ] $text match REJECTED  score={best_score:.2f}  overlap={ratio:.0%} (< {FAQ_KEYWORD_OVERLAP_MIN_RATIO:.0%})")
                    else:
                        # No extractable keywords — trust textScore alone
                        faq_match = best
                else:
                    print(f"[FAQ] $text score {best_score:.2f} below threshold {FAQ_TEXT_SCORE_THRESHOLD}")
        except Exception:
            pass  # $text index may not be ready

        # 1b. Fallback: regex-based keyword search with strict overlap
        if faq_match is None:
            user_kws = _extract_keywords(query)
            if user_kws:
                regex_pattern = "|".join(re.escape(k) for k in user_kws)
                candidates = list(
                    faq_repository.find(
                        {"question_text": {"$regex": regex_pattern, "$options": "i"}},
                        {"faq_id": 1, "question_text": 1, "static_answer": 1, "category": 1, "template_id": 1},
                    )
                )
                if candidates:
                    # Score each candidate
                    scored = []
                    for c in candidates:
                        hits, ratio = _keyword_overlap_score(user_kws, c.get("question_text", ""))
                        scored.append((hits, ratio, c))
                    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
                    best_hits, best_ratio, best_candidate = scored[0]

                    # Strict acceptance: ≥50% overlap AND (≥2 hits OR single long keyword)
                    if best_ratio >= FAQ_KEYWORD_OVERLAP_MIN_RATIO:
                        if best_hits >= 2 or (best_hits == 1 and len(user_kws) == 1 and len(user_kws[0]) >= 5):
                            faq_match = best_candidate
                            print(f"[FAQ] Regex match accepted  hits={best_hits}  overlap={best_ratio:.0%}")
                        else:
                            print(f"[FAQ] Regex match REJECTED  hits={best_hits} < 2 and keyword too short")
                    else:
                        print(f"[FAQ] Regex match REJECTED  overlap={best_ratio:.0%} < {FAQ_KEYWORD_OVERLAP_MIN_RATIO:.0%}")

        # ── Return FAQ answer if matched ──
        if faq_match is not None:
            log_entry["match_type"] = "exact"
            log_entry["evidence_id"] = f"ev_{uuid.uuid4().hex[:8]}"
            log_entry["source_reference"] = "FAQ Repository"
            log_entry["confidence_score"] = 0.98
            evidence_logs.insert_one(log_entry)

            # Process 3.0 (Task 2): Dynamic format lookup via FK chain
            # FAQ → template_id → question_template.answer_id → answer_template.format_type
            format_type = "Text"  # default fallback
            faq_template_id = faq_match.get("template_id")
            if faq_template_id:
                qt_doc = question_templates.find_one({"intent": faq_template_id}) or \
                         question_templates.find_one({"query_log_id": faq_template_id})
                if qt_doc and qt_doc.get("answer_id"):
                    ans_doc = answer_templates.find_one({"answer_id": qt_doc["answer_id"]})
                    if ans_doc:
                        format_type = ans_doc.get("format_type", "Text")
                else:
                    # Direct lookup by format_type as a simpler fallback
                    ans_doc = answer_templates.find_one({"format_type": "Text"})
                    if ans_doc:
                        format_type = ans_doc.get("format_type", "Text")

            # Task 4: Module 49 silent background log
            asyncio.ensure_future(send_log_to_module_49(log_entry))

            return {
                "answer": faq_match.get("static_answer", "Answer not found."),
                "confidence_score": 0.98,
                "citation": f"FAQ Database – {faq_match.get('category', 'General')}",
                "format_type": format_type,
                "timestamp": log_entry["timestamp"].isoformat() + "Z",
            }

        # ────────────────────────────────────────────────────────────────
        # PROCESS 2.0 — Match Intent Templates + Fetch Module 17 Data
        # ────────────────────────────────────────────────────────────────
        templates = list(question_templates.find({}))
        for template in templates:
            pattern = template.get("pattern", "")
            if pattern and re.search(pattern, query, re.IGNORECASE):
                intent = template.get("intent", "unknown")
                question_type = template.get("question_type", "Factual")
                data_source_required = template.get("data_source_required", "Unknown_DB")
                template_answer_id = template.get("answer_id", "ans_tmpl_text")

                # Task 3: Realistic Module 17 call with mock fallback
                parsed_entities = {
                    "data_source": data_source_required,
                    "query": query,
                    "intent": intent,
                }
                mock_answer = fetch_module_17_data(intent, parsed_entities)

                # Evidence log
                log_entry["match_type"] = "intent"
                log_entry["evidence_id"] = f"ev_{uuid.uuid4().hex[:8]}"
                log_entry["source_reference"] = f"Module 17 ({data_source_required})"
                log_entry["confidence_score"] = 0.85
                evidence_logs.insert_one(log_entry)

                # Process 3.0 (Task 2): Dynamic format lookup via answer_id FK
                ans_template = answer_templates.find_one({"answer_id": template_answer_id})
                if isinstance(ans_template, dict):
                    chosen_format = ans_template.get("format_type", "Text")
                else:
                    chosen_format = "Text"

                # Task 4: Module 49 silent background log
                asyncio.ensure_future(send_log_to_module_49(log_entry))

                return {
                    "answer": mock_answer,
                    "confidence_score": 0.85,
                    "citation": f"Intent Match: {intent} ({question_type})",
                    "format_type": chosen_format,
                    "timestamp": log_entry["timestamp"].isoformat() + "Z",
                }

        # ────────────────────────────────────────────────────────────────
        # FALLBACK — Unrecognised query
        # ────────────────────────────────────────────────────────────────
        log_entry["match_type"] = "none"
        log_entry["evidence_id"] = f"ev_{uuid.uuid4().hex[:8]}"
        log_entry["source_reference"] = "None"
        log_entry["confidence_score"] = 0.0
        evidence_logs.insert_one(log_entry)

        # Task 4: Module 49 silent background log
        asyncio.ensure_future(send_log_to_module_49(log_entry))

        return {
            "answer": (
                "⚠️ I am a Clinical Assistant. Your query doesn't match our clinical records or intent templates. "
                "Please enter a proper medical query, such as 'What is the standard dosage for Aspirin?' "
                "or 'Show patient history'."
            ),
            "confidence_score": 0.0,
            "citation": "None (Unrecognized Query)",
            "format_type": "Text",
            "timestamp": log_entry["timestamp"].isoformat() + "Z",
        }

    except Exception as e:
        log_entry["error"] = str(e)
        evidence_logs.insert_one(log_entry)
        raise HTTPException(status_code=500, detail=str(e))
