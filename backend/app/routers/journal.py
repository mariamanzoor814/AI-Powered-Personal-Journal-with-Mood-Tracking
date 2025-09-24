# backend/app/routers/journal.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import models
from app.db.database import get_db
from app.auth.auth import get_current_user
import uuid
from fastapi import HTTPException


router = APIRouter(prefix="/journals", tags=["journals"])

class JournalEntryUpdate(BaseModel):
    content: str
    
class JournalEntryCreate(BaseModel):
    content: str

@router.post("/")
def create_journal_entry(
    entry: JournalEntryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    new_entry = models.JournalEntry(user_id=current_user.id, content=entry.content)
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return {"msg": "Journal entry created", "entry": {"id": new_entry.id, "content": new_entry.content}}

@router.get("/")
def get_journal_entries(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    entries = db.query(models.JournalEntry).filter(models.JournalEntry.user_id == current_user.id).all()
    return {"entries": [
        {"id": e.id, "content": e.content, "created_at": e.created_at}
        for e in entries
    ]}

@router.delete("/{entry_id}")
def delete_journal_entry(
    entry_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    entry = db.query(models.JournalEntry).filter(
        models.JournalEntry.id == entry_id,
        models.JournalEntry.user_id == current_user.id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    db.delete(entry)
    db.commit()
    return {"msg": "Journal entry deleted"}

@router.put("/{entry_id}")
def update_journal_entry(
    entry_id: uuid.UUID,
    entry_update: JournalEntryUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    entry = db.query(models.JournalEntry).filter(
        models.JournalEntry.id == entry_id,
        models.JournalEntry.user_id == current_user.id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    entry.content = entry_update.content
    db.commit()
    db.refresh(entry)
    return {"msg": "Journal entry updated", "entry": {"id": entry.id, "content": entry.content}}

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
