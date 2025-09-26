# backend/app/routers/journal.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import models
from app.db.database import get_db
from app.auth.auth import get_current_user
from app.services import nlp  # HF API client wrapper
import uuid
from datetime import datetime

router = APIRouter(prefix="/journals", tags=["journals"])


class JournalEntryCreate(BaseModel):
    content: str


class JournalEntryUpdate(BaseModel):
    content: str


# ----------------- CREATE -----------------
@router.post("/", status_code=201)
def create_journal_entry(
    entry: JournalEntryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # create entry
    new_entry = models.JournalEntry(user_id=current_user.id, content=entry.content)
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    # analyze mood via HF API
    try:
        analysis = nlp.analyze_mood(new_entry.content)
    except Exception:
        analysis = {"sentiment": "unknown", "emotion": "unknown", "score": 0.0}

    # persist mood analysis linked to this entry
    new_mood = models.MoodAnalysis(
        user_id=current_user.id,
        entry_id=new_entry.id,
        sentiment=analysis.get("sentiment", "unknown"),
        emotion=analysis.get("emotion", "unknown"),
        score=analysis.get("score", 0.0),
    )
    db.add(new_mood)
    db.commit()
    db.refresh(new_mood)

    # generate recommendation (now passes score too)
    recommendation = nlp.get_recommendation(
        analysis.get("sentiment"),
        analysis.get("emotion"),
        analysis.get("score", 0.0),
    )

    return {
        "msg": "Journal entry created",
        "entry": {
            "id": new_entry.id,
            "content": new_entry.content,
            "created_at": new_entry.created_at,
            "mood_analysis": {
                "id": new_mood.id,
                "sentiment": new_mood.sentiment,
                "emotion": new_mood.emotion,
                "score": new_mood.score,
                "created_at": new_mood.created_at,
                "recommendation": recommendation,
            },
        },
    }


# ----------------- GET -----------------
@router.get("/")
def get_journal_entries(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    entries = (
        db.query(models.JournalEntry)
        .filter(models.JournalEntry.user_id == current_user.id)
        .order_by(models.JournalEntry.created_at.desc())
        .all()
    )

    out = []
    for e in entries:
        mood = None
        if e.mood_analysis:
            m = e.mood_analysis
            mood = {
                "id": m.id,
                "sentiment": m.sentiment,
                "emotion": m.emotion,
                "score": m.score,
                "created_at": m.created_at,
                "recommendation": nlp.get_recommendation(m.sentiment, m.emotion, m.score),
            }
        out.append(
            {
                "id": e.id,
                "content": e.content,
                "created_at": e.created_at,
                "updated_at": e.updated_at,
                "mood_analysis": mood,
            }
        )
    return {"entries": out}


# ----------------- DELETE -----------------
@router.delete("/{entry_id}")
def delete_journal_entry(
    entry_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    entry = (
        db.query(models.JournalEntry)
        .filter(
            models.JournalEntry.id == entry_id,
            models.JournalEntry.user_id == current_user.id,
        )
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    db.delete(entry)
    db.commit()
    return {"msg": "Journal entry deleted"}


# ----------------- UPDATE -----------------
@router.put("/{entry_id}")
def update_entry(
    entry_id: uuid.UUID,
    entry_data: JournalEntryUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    entry = (
        db.query(models.JournalEntry)
        .filter_by(id=entry_id, user_id=current_user.id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    entry.content = entry_data.content
    entry.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(entry)

    # re-run Hugging Face inference
    try:
        analysis = nlp.analyze_mood(entry.content)
    except Exception:
        analysis = {"sentiment": "unknown", "emotion": "unknown", "score": 0.0}

    # update mood_analysis row (UNIQUE ensures one per entry)
    mood = db.query(models.MoodAnalysis).filter_by(entry_id=entry.id).first()
    if mood:
        mood.sentiment = analysis["sentiment"]
        mood.emotion = analysis["emotion"]
        mood.score = analysis["score"]
        mood.created_at = datetime.utcnow()
        db.commit()
        db.refresh(mood)

    # generate recommendation (now passes score too)
    recommendation = nlp.get_recommendation(
        analysis.get("sentiment"),
        analysis.get("emotion"),
        analysis.get("score", 0.0),
    )

    return {
        "msg": "Entry and analysis updated successfully",
        "entry": {
            "id": entry.id,
            "content": entry.content,
            "updated_at": entry.updated_at,
            "mood_analysis": {
                "id": mood.id if mood else None,
                "sentiment": analysis.get("sentiment"),
                "emotion": analysis.get("emotion"),
                "score": analysis.get("score"),
                "created_at": mood.created_at if mood else None,
                "recommendation": recommendation,
            },
        },
    }
