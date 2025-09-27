# AI-Powered Personal Journal
#frontend  : https://mariamanzoor814-ai-powered-persona-frontendstreamlit-app-gaype0.streamlit.app/

An AI-powered personal journaling platform that allows users to write daily journals, track moods, and receive emotional insights.
This project integrates NLP, translation, and sentiment analysis to provide users with meaningful reflections on their mental well-being.

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

