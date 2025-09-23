# Router for journal-related endpoints.
# backend/app/routers/journal.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import models
from app.db.database import get_db
from app.auth.auth import get_current_user

router = APIRouter(prefix="/journals", tags=["journals"])

# Create a journal entry
@router.post("/")
def create_journal_entry(content: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    new_entry = models.JournalEntry(user_id=current_user.id, content=content)
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return {"msg": "Journal entry created", "entry": {"id": new_entry.id, "content": new_entry.content}}

# Get all journal entries for the logged-in user
@router.get("/")
def get_journal_entries(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    entries = db.query(models.JournalEntry).filter(models.JournalEntry.user_id == current_user.id).all()
    return {"entries": [{"id": e.id, "content": e.content, "created_at": e.created_at} for e in entries]}


# inside backend/app/routers/journal.py

# Save a mood entry
@router.post("/mood")
def log_mood(mood: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    new_mood = models.MoodAnalysis(user_id=current_user.id, mood=mood)
    db.add(new_mood)
    db.commit()
    db.refresh(new_mood)
    return {"msg": "Mood logged", "mood": {"id": new_mood.id, "mood": new_mood.mood}}

# Get mood history
@router.get("/mood")
def get_mood_history(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    moods = db.query(models.MoodAnalysis).filter(models.MoodAnalysis.user_id == current_user.id).all()
    return {"moods": [{"id": m.id, "mood": m.mood, "created_at": m.created_at} for m in moods]}
