# from sqlalchemy.orm import Session, joinedload
# from app.db import models
# from app.schemas.journal_schemas import JournalCreate
# from app.services.nlp import analyze_mood

# def create_journal_entry(db: Session, entry: JournalCreate, user_id: uuid.UUID) -> models.JournalEntry:
#     """
#     Creates a new journal entry, performs mood analysis, and saves both records.
#     """
#     # 1. Create the Journal Entry
#     db_entry = models.JournalEntry(
#         text=entry.text, 
#         user_id=user_id
#     )
#     db.add(db_entry)
#     db.flush()  # Use flush to get the ID before committing

#     # 2. Perform Mood Analysis
#     analysis_data = analyze_mood(entry.text)

#     # 3. Create the Mood Analysis Record, linked to the new entry
#     db_analysis = models.MoodAnalysis(
#         entry_id=db_entry.id,
#         sentiment=analysis_data["sentiment"],
#         emotion=analysis_data["emotion"],
#         score=analysis_data["score"]
#     )
#     db.add(db_analysis)
    
#     # 4. Commit both records and refresh to get the complete object
#     db.commit()
#     db.refresh(db_entry)
#     return db_entry

# def get_journal_entries(db: Session, user_id: uuid.UUID) -> list[models.JournalEntry]:
#     """
#     Fetches all journal entries for a user, eagerly loading the mood analysis.
#     """
#     return db.query(models.JournalEntry).filter(
#         models.JournalEntry.user_id == user_id
#     ).options(joinedload(models.JournalEntry.mood_analysis)).all()

# def delete_journal_entry(db: Session, entry_id: uuid.UUID, user_id: uuid.UUID):
#     """
#     Deletes a journal entry and its associated mood analysis record.
#     """
#     entry = db.query(models.JournalEntry).filter(
#         models.JournalEntry.id == entry_id,
#         models.JournalEntry.user_id == user_id
#     ).first()
#     if entry:
#         db.delete(entry)
#         db.commit()
#     return entry

# def update_journal_entry(db: Session, entry_id: uuid.UUID, entry_update: dict, user_id: uuid.UUID) -> models.JournalEntry:
#     """
#     Updates a journal entry and re-runs mood analysis.
#     """
#     entry = db.query(models.JournalEntry).filter(
#         models.JournalEntry.id == entry_id,
#         models.JournalEntry.user_id == user_id
#     ).first()
#     if entry:
#         entry.text = entry_update.get("text", entry.text)
        
#         # Re-run mood analysis on update
#         analysis_data = analyze_mood(entry.text)
        
#         # Update or create the associated mood analysis record
#         if entry.mood_analysis:
#             db.query(models.MoodAnalysis).filter(models.MoodAnalysis.entry_id == entry.id).update({
#                 "sentiment": analysis_data["sentiment"],
#                 "emotion": analysis_data["emotion"],
#                 "score": analysis_data["score"]
#             })
#         else:
#             db_analysis = models.MoodAnalysis(
#                 entry_id=entry.id,
#                 sentiment=analysis_data["sentiment"],
#                 emotion=analysis_data["emotion"],
#                 score=analysis_data["score"]
#             )
#             db.add(db_analysis)

#         db.commit()
#         db.refresh(entry)
#     return entry
