import streamlit as st
import requests
import pandas as pd
import altair as alt
import os

# --- Configuration ---
API_BASE = "http://127.0.0.1:8000"
TOKEN_FILE = "token.txt"

# --- State Management ---
def initialize_session_state():
    """Initializes session state variables if they don't exist."""
    if "token" not in st.session_state:
        st.session_state["token"] = load_token()
    if "username" not in st.session_state:
        st.session_state["username"] = None
    if "page" not in st.session_state:
        st.session_state["page"] = "home"
    if "email_for_verification" not in st.session_state:
        st.session_state["email_for_verification"] = ""


# --- Token Management ---
def save_token(token: str):
    """Save the token to a local file."""
    with open(TOKEN_FILE, "w") as f:
        f.write(token)

def load_token():
    """Load the token from a local file if it exists."""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip() or None
    return None

def clear_token():
    """Delete the token from the file."""
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)

# --- API Helper Functions ---
def auth_headers():
    """Returns authorization headers if a token is available."""
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}

def post_register(username, email, password):
    url = f"{API_BASE}/users/register"
    return requests.post(url, json={"username": username, "email": email, "password": password})

def post_verify(email, otp):
    url = f"{API_BASE}/users/verify"
    return requests.post(url, json={"email": email, "otp": otp})

def post_login(email, password):
    url = f"{API_BASE}/users/login"
    return requests.post(url, json={"email": email, "password": password})

def create_entry(text):
    url = f"{API_BASE}/journals/"
    return requests.post(url, json={"content": text}, headers=auth_headers())

def list_entries():
    url = f"{API_BASE}/journals/"
    return requests.get(url, headers=auth_headers())

def delete_entry(entry_id):
    url = f"{API_BASE}/journals/{entry_id}"
    return requests.delete(url, headers=auth_headers())

def edit_entry(entry_id, new_content):
    url = f"{API_BASE}/journals/{entry_id}"
    return requests.put(url, json={"content": new_content}, headers=auth_headers())

# --- UI Page Rendering Functions ---

def render_sidebar():
    """Renders the sidebar navigation based on login state."""
    with st.sidebar:
        st.title("Menu")
        if st.session_state.get("token"):
            # Logged-in view
            if st.button("Journal"):
                st.session_state.page = "journal"
                st.rerun()
            if st.button("Dashboard"):
                st.session_state.page = "dashboard"
                st.rerun()
            if st.button("Logout"):
                st.session_state.token = None
                st.session_state.username = None
                clear_token()
                st.session_state.page = "home"
                st.success("Logged out.")
                st.rerun()
        else:
            # Logged-out view
            if st.button("Home"):
                st.session_state.page = "home"
                st.rerun()
            if st.button("Register"):
                st.session_state.page = "register"
                st.rerun()
            if st.button("Login"):
                st.session_state.page = "login"
                st.rerun()

def render_home_page():
    st.header("Welcome to AI Journal")
    st.write("Your personal space to write, reflect, and track your mood over time.")
    st.write("Please use the sidebar to Register or Login.")

def render_register_page():
    st.header("Register")
    with st.form("register_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Create account")

        if submitted:
            r = post_register(username, email, password)
            if r.status_code == 201:
                st.success("Registration successful! Please check your email for a verification OTP.")
                st.session_state.email_for_verification = email
                st.session_state.page = "verify"
                st.rerun()
            else:
                try:
                    st.error(r.json().get("detail", "An unknown error occurred."))
                except requests.exceptions.JSONDecodeError:
                    st.error(f"Server error: {r.text}")

def render_verify_page():
    st.header("Verify Your Account")
    email = st.text_input("Email", value=st.session_state.get("email_for_verification", ""))
    otp = st.text_input("OTP Code")

    if st.button("Verify"):
        r = post_verify(email, otp)
        if r.status_code == 200:
            st.success("Account verified successfully! You can now log in.")
            st.session_state.page = "login"
            st.rerun()
        else:
            try:
                st.error(r.json().get("detail", "Verification failed."))
            except requests.exceptions.JSONDecodeError:
                st.error(f"Server error: {r.text}")

def render_login_page():
    st.header("Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            r = post_login(email, password)
            if r.status_code == 200:
                token = r.json().get("access_token")
                st.session_state.token = token
                st.session_state.username = email
                save_token(token)
                st.session_state.page = "journal"
                st.rerun()
            else:
                try:
                    st.error(r.json().get("detail", "Login failed."))
                except requests.exceptions.JSONDecodeError:
                    st.error(f"Server error: {r.text}")

def render_journal_page():
    if not st.session_state.get("token"):
        st.warning("Please log in to access your journal.")
        return

    st.header("Write a New Journal Entry")
    text = st.text_area("What's on your mind?", height=200, key="journal_text_area")
    if st.button("Save Entry"):
        r = create_entry(text)
        if r.status_code in [200, 201]:
            st.success("Entry saved successfully.")
            st.rerun()
        else:
            try:
                st.error(r.json().get("detail", "Failed to save entry."))
            except requests.exceptions.JSONDecodeError:
                st.error(f"Server error: {r.text}")

    st.markdown("---")
    st.subheader("Your Past Entries")
    r = list_entries()
    if r.status_code == 200:
        entries = sorted(r.json().get("entries", []), key=lambda x: x.get("created_at", ""), reverse=True)
        for e in entries:
            with st.container():
                st.write(f"**{e['created_at']}** — {e['content']}")
                if e.get("mood_analysis"):
                    m = e["mood_analysis"]
                    st.caption(f"Sentiment: {m['sentiment']} ({m['score']:.2f}), Emotion: {m['emotion']}")

                # Check if we are in edit mode for this specific entry
                if st.session_state.get(f"edit_mode_{e['id']}", False):
                    new_content = st.text_area("Edit entry", value=e['content'], key=f"edit-area-{e['id']}")
                    
                    # Place Save and Cancel buttons horizontally
                    edit_col1, edit_col2 = st.columns(2)
                    with edit_col1:
                        if st.button(f"Save Edit", key=f"save-edit-{e['id']}"):
                            er = edit_entry(e['id'], new_content)
                            if er.status_code == 200:
                                st.success("Entry updated.")
                                del st.session_state[f"edit_mode_{e['id']}"]
                                st.rerun()
                            else:
                                st.error("Edit failed.")
                    with edit_col2:
                        if st.button(f"Cancel Edit", key=f"cancel-edit-{e['id']}"):
                            del st.session_state[f"edit_mode_{e['id']}"]
                            st.rerun()
                else:
                    # Place Edit and Delete buttons horizontally
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Edit", key=f"edit-{e['id']}"):
                            st.session_state[f"edit_mode_{e['id']}"] = True
                            st.rerun()
                    with col2:
                        if st.button(f"Delete", key=f"del-{e['id']}"):
                            delete_entry(e['id'])
                            st.rerun()
                st.markdown("---")

def render_dashboard_page():
    if not st.session_state.get("token"):
        st.warning("Please log in to view the dashboard.")
        return

    st.header("Mood Dashboard")
    r = list_entries()
    if r.status_code == 200:
        entries = r.json().get("entries", [])
        rows = []
        for e in entries:
            if e.get("mood_analysis"):
                rows.append({
                    "date": e["created_at"][:10],
                    "sentiment_score": e["mood_analysis"].get("score", 0),
                    "sentiment": e["mood_analysis"].get("sentiment", "UNKNOWN")
                })

        if rows:
            df = pd.DataFrame(rows)
            df["date"] = pd.to_datetime(df["date"])
            chart = alt.Chart(df).mark_line(point=True).encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y("sentiment_score:Q", title="Sentiment Score"),
                tooltip=["date", "sentiment", "sentiment_score"]
            ).properties(
                title="Sentiment Score Over Time",
                width=700,
                height=400
            ).interactive()
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No mood data available. Write some journal entries first!")
    else:
        try:
            st.error(r.json().get("detail", "Could not load dashboard data."))
        except requests.exceptions.JSONDecodeError:
            st.error(f"Server error: {r.text}")


# --- Main App Logic ---
def main():
    st.set_page_config(page_title="AI Journal", layout="centered", page_icon="📝")
    st.title("AI-Powered Personal Journal")
    
    initialize_session_state()
    render_sidebar()

    # Page router
    page = st.session_state.page
    if page == "home":
        render_home_page()
    elif page == "register":
        render_register_page()
    elif page == "verify":
        render_verify_page()
    elif page == "login":
        render_login_page()
    elif page == "journal":
        render_journal_page()
    elif page == "dashboard":
        render_dashboard_page()
    else:
        st.session_state.page = "home"
        st.rerun()

if __name__ == "__main__":
    main()


