# backend/app/main.py
from fastapi import FastAPI
from app.db import models
from app.db.database import engine
from app.routers import users, journal   # 👈 add journal router

app = FastAPI(title="AI Journal API 🚀")

# Create tables
models.Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(users.router)
app.include_router(journal.router)   # 👈 include here

@app.get("/")
def root():
    return {"message": "AI Journal API is running 🚀"}
