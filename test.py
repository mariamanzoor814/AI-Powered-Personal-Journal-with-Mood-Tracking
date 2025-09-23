# test_db.py
from backend.app.db.database import engine

try:
    conn = engine.connect()
    print("✅ Database connection successful!")
    conn.close()
except Exception as e:
    print("❌ Database connection failed:", e)
