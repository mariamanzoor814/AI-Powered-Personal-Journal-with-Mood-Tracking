---
title: AI-Powered Personal Journal
sdk: docker
app_port: 7860
---

# AI-Powered Personal Journal
#frontend  : https://mariamanzoor814-ai-powered-persona-frontendstreamlit-app-gaype0.streamlit.app/

An AI-powered personal journaling platform that allows users to write daily journals, track moods, and receive emotional insights.
This project integrates NLP, translation, and sentiment analysis to provide users with meaningful reflections on their mental well-being.

---
#Gallery

<img width="1920" height="1040" alt="p1" src="https://github.com/user-attachments/assets/f700c4e1-6c5b-4b99-aaa7-f2c813ce78ad" />
<img width="1920" height="1040" alt="p2" src="https://github.com/user-attachments/assets/40ac3f44-1e42-42b3-940f-507d3cbc8e00" />
<img width="1920" height="1040" alt="p3" src="https://github.com/user-attachments/assets/74e8e7d4-cb63-4f2e-b946-c2f05dea970a" />
<img width="1920" height="1040" alt="p4" src="https://github.com/user-attachments/assets/e6b9adff-2daf-4bad-b995-27fe07ad6541" />
<img width="1920" height="1040" alt="p5" src="https://github.com/user-attachments/assets/c31e146b-b2b2-40ca-b666-e77f3c10c0c9" />
<img width="1920" height="1040" alt="p6" src="https://github.com/user-attachments/assets/96c0860f-6c0d-4867-871a-c364adf339e8" />


---

## ⚙️ Tech Stack

### 🎨 Frontend
- **Streamlit** — Interactive frontend UI

### 🔧 Backend
- **FastAPI** — RESTful backend
- **PostgreSQL** — Relational database
- **SQLAlchemy ORM** — Database models & queries
- **Alembic** — Database migrations

### 🤖 AI & NLP
- **Hugging Face Inference API**
  - Sentiment Analysis: `distilbert-base-uncased-finetuned-sst-2-english`
  - Emotion Detection: `j-hartmann/emotion-english-distilroberta-base`
- **DeepL API** — Language detection & translation

### 🔐 Authentication & Security
- **JWT (JSON Web Tokens)** — Secure authentication
- **Passlib & bcrypt** — Password hashing

