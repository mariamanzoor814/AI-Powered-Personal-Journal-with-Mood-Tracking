# frontend/streamlit_app.py
import streamlit as st
import requests
import pandas as pd
import altair as alt

API_BASE = "http://127.0.0.1:8000"


# ---------- API Helpers ----------
def post_register(username, email, password):
    url = f"{API_BASE}/users/register"
    return requests.post(url, json={"username": username, "email": email, "password": password})

def post_login(username, password):
    url = f"{API_BASE}/users/login"
    data = {"username": username, "password": password}
    return requests.post(url, data=data)  # FastAPI handles form-data here

def auth_headers():
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}

def create_entry(text):
    url = f"{API_BASE}/journals/"
    return requests.post(url, json={"text": text}, headers=auth_headers())

def list_entries():
    url = f"{API_BASE}/journals/"
    return requests.get(url, headers=auth_headers())

def delete_entry(entry_id):
    url = f"{API_BASE}/journals/{entry_id}"
    return requests.delete(url, headers=auth_headers())


# ---------- Streamlit UI ----------
st.set_page_config(page_title="AI Journal", layout="centered", page_icon="📝")

if "token" not in st.session_state:
    st.session_state["token"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None

st.title("AI-Powered Personal Journal — Mood Tracking")

menu = st.sidebar.selectbox("Menu", ["Home", "Register", "Login", "Journal", "Dashboard", "Logout"])

# ---------- Register ----------
if menu == "Register":
    st.header("Register")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Create account"):
        r = post_register(username, email, password)
        if r.status_code == 201:
            st.success("Registered. Now login.")
        else:
            try:
                st.error(r.json().get("detail", r.text))
            except Exception:
                st.error(r.text)

# ---------- Login ----------
elif menu == "Login":
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        r = post_login(username, password)
        if r.status_code == 200:
            token = r.json().get("access_token")
            st.session_state["token"] = token
            st.session_state["username"] = username
            st.success("Logged in.")
        else:
            try:
                st.error(r.json().get("detail", r.text))
            except Exception:
                st.error(r.text)

# ---------- Journal ----------
elif menu == "Journal":
    if not st.session_state["token"]:
        st.warning("Log in first.")
    else:
        st.header("Write a Journal Entry")
        text = st.text_area("What's on your mind?", height=200)
        if st.button("Save Entry"):
            r = create_entry(text)
            if r.status_code == 201:
                st.success("Saved.")
            else:
                try:
                    st.error(r.json().get("detail", r.text))
                except Exception:
                    st.error(r.text)

        st.markdown("---")
        st.subheader("Your Entries")
        r = list_entries()
        if r.status_code == 200:
            entries = r.json()
            for e in entries:
                st.write(f"**{e['created_at']}** — {e['text']}")
                if e.get("mood_analysis"):
                    m = e["mood_analysis"]
                    st.caption(f"Sentiment: {m['sentiment']} ({m['score']:.2f}), Emotion: {m['emotion']}")
                if st.button(f"Delete {e['id']}", key=f"del-{e['id']}"):
                    dr = delete_entry(e['id'])
                    if dr.status_code == 204:
                        st.experimental_rerun()
                    else:
                        st.error("Delete failed.")
        else:
            try:
                st.error(r.json().get("detail", r.text))
            except Exception:
                st.error(r.text)

# ---------- Dashboard ----------
elif menu == "Dashboard":
    if not st.session_state["token"]:
        st.warning("Log in first.")
    else:
        st.header("Mood Dashboard")
        r = list_entries()
        if r.status_code == 200:
            entries = r.json()
            rows = []
            for e in entries:
                created = e["created_at"]
                rows.append({
                    "date": created[:10],
                    "sentiment_score": e.get("mood_analysis", {}).get("score", 0),
                    "sentiment": e.get("mood_analysis", {}).get("sentiment", "UNKNOWN")
                })
            if rows:
                df = pd.DataFrame(rows)
                df["date"] = pd.to_datetime(df["date"])
                chart = alt.Chart(df).mark_line(point=True).encode(
                    x="date:T",
                    y="sentiment_score:Q",
                    tooltip=["date", "sentiment", "sentiment_score"]
                ).properties(width=700, height=300)
                st.altair_chart(chart)
            else:
                st.info("No entries yet.")
        else:
            try:
                st.error(r.json().get("detail", r.text))
            except Exception:
                st.error(r.text)

# ---------- Logout ----------
elif menu == "Logout":
    st.session_state["token"] = None
    st.session_state["username"] = None
    st.success("Logged out.")
