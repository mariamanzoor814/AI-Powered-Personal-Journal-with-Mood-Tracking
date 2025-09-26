# models.py
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Text, Boolean
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # relationships
    entries = relationship("JournalEntry", back_populates="user", cascade="all, delete-orphan")
    moods = relationship("MoodAnalysis", back_populates="user", cascade="all, delete-orphan")

    # new fields
    is_verified = Column(Boolean, default=False)
    otp_code = Column(String, nullable=True)
    otp_expiry = Column(DateTime, nullable=True)


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)

    # relationships
    user = relationship("User", back_populates="entries")
    mood_analysis = relationship(
        "MoodAnalysis",
        back_populates="entry",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class MoodAnalysis(Base):
    __tablename__ = "mood_analysis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    entry_id = Column(
        UUID(as_uuid=True),
        ForeignKey("journal_entries.id", ondelete="CASCADE"),
        nullable=True
    )
    sentiment = Column(String, nullable=False)
    emotion = Column(String, nullable=False)
    score = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # relationships
    user = relationship("User", back_populates="moods")
    entry = relationship("JournalEntry", back_populates="mood_analysis")
