# Pydantic schemas for data validation.
# backend/app/schemas/journal_schemas.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MoodAnalysisBase(BaseModel):
    sentiment: str
    emotion: str
    score: float

class MoodAnalysisOut(MoodAnalysisBase):
    id: int
    entry_id: int

    class Config:
        orm_mode = True

class JournalBase(BaseModel):
    text: str

class JournalCreate(JournalBase):
    pass

class JournalUpdate(BaseModel):
    text: Optional[str] = None

class JournalOut(BaseModel):
    id: int
    user_id: int
    text: str
    created_at: datetime
    updated_at: Optional[datetime]
    mood_analysis: Optional[MoodAnalysisOut] = None

    class Config:
        orm_mode = True
