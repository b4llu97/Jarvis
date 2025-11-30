from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import database
import tools
import os
from database import get_db, init_db
from feedback_db import FeedbackDB

app = FastAPI(title="Jarvis Toolserver", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

# Initialize feedback database
FEEDBACK_DB_PATH = os.getenv("FEEDBACK_DB_PATH", "/app/data/feedback.db")
feedback_db = FeedbackDB(FEEDBACK_DB_PATH)

class FactRequest(BaseModel):
    value: str

class FactResponse(BaseModel):
    key: str
    value: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    n_results: int = 5

class DocumentRequest(BaseModel):
    text: str
    metadata: Optional[dict] = None

class FeedbackRequest(BaseModel):
    query: str
    response: str
    rating: int  # 1-5
    comment: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None

class CorrectionRequest(BaseModel):
    query: str
    wrong_response: str
    correct_response: str
    context: Optional[str] = None

class PreferenceRequest(BaseModel):
    key: str
    value: str


class SmartHomeListDevicesRequest(BaseModel):
    domain: str


class SmartHomeEntityRequest(BaseModel):
    entity_id: str


@app.get("/")
def root():
    return {"service": "Jarvis Toolserver", "status": "running"}

@app.get("/v1/tools")
def get_tools():
    return {"tools": tools.get_tool_definitions()}

@app.get("/v1/facts/{key}", response_model=FactResponse)
def get_fact(key: str, db: Session = Depends(get_db)):
    fact = database.get_fact(db, key)
    if not fact:
        raise HTTPException(status_code=404, detail=f"Fact with key '{key}' not found")
    return fact.to_dict()

@app.put("/v1/facts/{key}", response_model=FactResponse)
def set_fact(key: str, request: FactRequest, db: Session = Depends(get_db)):
    fact = database.set_fact(db, key, request.value)
    return fact.to_dict()

@app.delete("/v1/facts/{key}")
def delete_fact(key: str, db: Session = Depends(get_db)):
    success = database.delete_fact(db, key)
    if not success:
        raise HTTPException(status_code=404, detail=f"Fact with key '{key}' not found")
    return {"message": f"Fact '{key}' deleted successfully"}

@app.get("/v1/facts", response_model=List[FactResponse])
def list_facts(db: Session = Depends(get_db)):
    facts = database.list_all_facts(db)
    return [fact.to_dict() for fact in facts]

@app.post("/v1/search")
def search_documents(request: SearchRequest):
    results = tools.search_docs(request.query, request.n_results)
    return {"query": request.query, "results": results}

@app.post("/v1/documents")
def add_document(request: DocumentRequest):
    success = tools.add_document(request.text, request.metadata)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add document")
    return {"message": "Document added successfully"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Feedback & Learning Endpoints

@app.post("/v1/feedback")
def add_feedback(request: FeedbackRequest):
    """Add user feedback for a conversation"""
    feedback_id = feedback_db.add_feedback(
        query=request.query,
        response=request.response,
        rating=request.rating,
        comment=request.comment,
        model=request.model,
        provider=request.provider
    )
    return {"message": "Feedback gespeichert", "feedback_id": feedback_id}

@app.post("/v1/corrections")
def add_correction(request: CorrectionRequest):
    """Add a user correction"""
    correction_id = feedback_db.add_correction(
        query=request.query,
        wrong_response=request.wrong_response,
        correct_response=request.correct_response,
        context=request.context
    )
    return {"message": "Korrektur gespeichert", "correction_id": correction_id}

@app.get("/v1/learning/context")
def get_learning_context(limit: int = 5):
    """Get learning context from feedback and corrections"""
    context = feedback_db.get_learning_context("", limit)
    return {"context": context}

@app.get("/v1/learning/statistics")
def get_learning_statistics():
    """Get feedback statistics"""
    stats = feedback_db.get_statistics()
    return stats

@app.get("/v1/feedback/negative")
def get_negative_feedback(limit: int = 20):
    """Get negative feedback for analysis"""
    feedback = feedback_db.get_negative_feedback(limit)
    return {"feedback": feedback}

@app.get("/v1/corrections")
def get_corrections(limit: int = 20):
    """Get all corrections"""
    corrections = feedback_db.get_corrections(limit)
    return {"corrections": corrections}

@app.post("/v1/preferences")
def set_preference(request: PreferenceRequest):
    """Set a user preference"""
    feedback_db.set_preference(request.key, request.value)
    return {"message": "Präferenz gespeichert"}

@app.get("/v1/preferences/{key}")
def get_preference(key: str):
    """Get a user preference"""
    value = feedback_db.get_preference(key)
    if value is None:
        raise HTTPException(status_code=404, detail=f"Preference '{key}' not found")
    return {"key": key, "value": value}

@app.get("/v1/preferences")
def get_all_preferences():
    """Get all user preferences"""
    preferences = feedback_db.get_all_preferences()
    return {"preferences": preferences}


@app.post("/v1/smarthome/list_devices")
def smarthome_list_devices(request: SmartHomeListDevicesRequest):
    """List all Smart Home devices of a specific type"""
    result = tools.smarthome_list_devices(request.domain)
    return result


@app.post("/v1/smarthome/turn_on")
def smarthome_turn_on(request: SmartHomeEntityRequest):
    """Turn on a Smart Home device"""
    result = tools.smarthome_turn_on(request.entity_id)
    return result


@app.post("/v1/smarthome/turn_off")
def smarthome_turn_off(request: SmartHomeEntityRequest):
    """Turn off a Smart Home device"""
    result = tools.smarthome_turn_off(request.entity_id)
    return result


@app.post("/v1/smarthome/get_status")
def smarthome_get_status(request: SmartHomeEntityRequest):
    """Get the status of a Smart Home device or sensor"""
    result = tools.smarthome_get_status(request.entity_id)
    return result
