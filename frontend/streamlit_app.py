import os
import streamlit as st
import requests
import pandas as pd
import altair as alt
from itertools import groupby
from datetime import datetime, timedelta


# --- Configuration ---
API_BASE = "http://127.0.0.1:8000"
REMEMBERED_USER_FILE = "remembered_user.txt"

# --- Utilities ---
def safe_rerun():
    try:
        if hasattr(st, "experimental_rerun"):
            return st.experimental_rerun()
        if hasattr(st, "rerun"):
            return st.rerun()
    except Exception:
        pass
    st.markdown('<script>window.location.reload()</script>', unsafe_allow_html=True)

def token_filename_for(username: str) -> str:
    safe_user = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in str(username))
    return f"token_{safe_user}.txt"

def save_token_for_user(username: str, token: str):
    if not username or not token:
        return
    fn = token_filename_for(username)
    try:
        with open(fn, "w") as f:
            f.write(token)
    except OSError:
        st.warning("Unable to persist token to disk.")

def load_token_for_user(username: str):
    if not username:
        return None
    fn = token_filename_for(username)
    if os.path.exists(fn):
        try:
            with open(fn, "r") as f:
                return f.read().strip() or None
        except OSError:
            return None
    return None

def clear_token_for_user(username: str):
    if not username:
        return
    fn = token_filename_for(username)
    try:
        if os.path.exists(fn):
            os.remove(fn)
    except OSError:
        pass

def remember_user(username: str):
    try:
        with open(REMEMBERED_USER_FILE, "w") as f:
            f.write(username)
    except OSError:
        pass

def load_remembered_user():
    try:
        if os.path.exists(REMEMBERED_USER_FILE):
            with open(REMEMBERED_USER_FILE, "r") as f:
                return f.read().strip() or None
    except OSError:
        return None
    return None

def clear_remembered_user():
    try:
        if os.path.exists(REMEMBERED_USER_FILE):
            os.remove(REMEMBERED_USER_FILE)
    except OSError:
        pass

# --- State Management ---
def initialize_session_state():
    if "token" not in st.session_state:
        st.session_state["token"] = None
    if "username" not in st.session_state:
        st.session_state["username"] = None
    if "page" not in st.session_state:
        st.session_state["page"] = "home"
    if "email_for_verification" not in st.session_state:
        st.session_state["email_for_verification"] = ""

    if not st.session_state.get("token"):
        remembered = load_remembered_user()
        if remembered:
            token = load_token_for_user(remembered)
            if token:
                st.session_state["username"] = remembered
                st.session_state["token"] = token

# --- Token Management ---
def save_token(token: str, username: str = None, remember: bool = False):
    if token:
        st.session_state["token"] = token
    if remember and username:
        save_token_for_user(username, token)
        remember_user(username)

def load_token():
    return st.session_state.get("token")

def clear_token():
    cur_user = st.session_state.get("username")
    st.session_state["token"] = None
    clear_remembered_user()
    if cur_user:
        clear_token_for_user(cur_user)

# --- API Helper Functions ---
def auth_headers():
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

# --- UI ---
def render_sidebar():
    with st.sidebar:
        st.markdown("<div style='margin-bottom:20px'></div>", unsafe_allow_html=True)
        st.title("Menu")
        if st.session_state.get("token"):
            if st.button("Journal", key="sidebar-journal"):
                st.session_state.page = "journal"
                safe_rerun()
            if st.button("Dashboard", key="sidebar-dashboard"):
                st.session_state.page = "dashboard"
                safe_rerun()
            if st.button("Logout", key="sidebar-logout"):
                clear_token()
                st.session_state.username = None
                st.session_state.page = "home"
                st.success("Logged out.")
                safe_rerun()
        else:
            if st.button("Home", key="sidebar-home"):
                st.session_state.page = "home"
                safe_rerun()
            if st.button("Register", key="sidebar-register"):
                st.session_state.page = "register"
                safe_rerun()
            if st.button("Login", key="sidebar-login"):
                st.session_state.page = "login"
                safe_rerun()
def render_home_page():
    st.markdown(
        """
        <style>
            .card {
                background: #f9f9ff;
                border-radius: 14px;
                padding: 1.2rem;
                margin: 1rem 0;
                box-shadow: 0 3px 8px rgba(0,0,0,0.07);
            }
            .card h3 {
                color: #5A67D8;
                font-family: Poppins, sans-serif;
                margin-bottom: 0.5rem;
            }
            .card p {
                color: #555;
                font-size: 0.95rem;
            }
            .cta {
                text-align: center;
                margin: 2rem 0;
            }
            .cta button {
                background: #5A67D8;
                color: white;
                font-family: Poppins, sans-serif;
                font-size: 1.1rem;
                padding: 0.9rem 1.8rem;
                border-radius: 10px;
                border: none;
                cursor: pointer;
                box-shadow: 0 3px 8px rgba(0,0,0,0.15);
                transition: background 0.2s ease-in-out;
            }
            .cta button:hover {
                background: #4C51BF;
            }
        </style>

        <div class="card">
            <h3>😊 Mood Analysis</h3>
            <p>Automatic sentiment and emotion scoring powered by AI.</p>
        </div>

        <div class="card">
            <h3>📊 Analytics Dashboard</h3>
            <p>View interactive charts of daily, weekly, and monthly trends.</p>
        </div>

        <div class="card">
            <h3>💡 Positive Prompts</h3>
            <p>Receive context-aware motivational messages every day.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 🚀 CTA button that actually changes the page
    col = st.container()
    with col:
        if st.button("🚀 Get Started – Register or Login", key="cta-btn"):
            st.session_state.page = "login"   # 👈 go straight to login
            safe_rerun()

def render_register_page():
    st.markdown("<h2 style='color:#5A67D8;'>Register</h2>", unsafe_allow_html=True)
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
                safe_rerun()
            else:
                try:
                    st.error(r.json().get("detail", "An unknown error occurred."))
                except requests.exceptions.JSONDecodeError:
                    st.error(f"Server error: {r.text}")

def render_verify_page():
    st.markdown("<h2 style='color:#5A67D8;'>Verify Your Account</h2>", unsafe_allow_html=True)
    email = st.text_input("Email", value=st.session_state.get("email_for_verification", ""))
    otp = st.text_input("OTP Code")

    if st.button("Verify", key="verify-btn"):
        r = post_verify(email, otp)
        if r.status_code == 200:
            st.success("Account verified successfully! You can now log in.")
            st.session_state.page = "login"
            safe_rerun()
        else:
            try:
                st.error(r.json().get("detail", "Verification failed."))
            except requests.exceptions.JSONDecodeError:
                st.error(f"Server error: {r.text}")

def render_login_page():
    st.markdown("<h2 style='color:#5A67D8;'>Login</h2>", unsafe_allow_html=True)
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        remember_me = st.checkbox("Remember me on this device")
        submitted = st.form_submit_button("Login")

        if submitted:
            r = post_login(email, password)
            if r.status_code == 200:
                token = r.json().get("access_token")
                st.session_state.token = token
                st.session_state.username = email
                save_token(token, username=email, remember=remember_me)
                st.session_state.page = "journal"
                safe_rerun()
            else:
                try:
                    st.error(r.json().get("detail", "Login failed."))
                except requests.exceptions.JSONDecodeError:
                    st.error(f"Server error: {r.text}")

def render_journal_page():
    if not st.session_state.get("token"):
        st.warning("Please log in to access your journal.")
        return

    st.markdown("<h2 style='color:#48BB78;'>My Journals</h2>", unsafe_allow_html=True)
    text = st.text_area("What's on your mind?", height=200, key="journal_text_area")
    if st.button("Save Entry", key="save-entry-btn"):
        r = create_entry(text)
        if r.status_code in [200, 201]:
            st.success("Entry saved successfully.")
            safe_rerun()
        else:
            try:
                st.error(r.json().get("detail", "Failed to save entry."))
            except requests.exceptions.JSONDecodeError:
                st.error(f"Server error: {r.text}")

    st.markdown("---")

    # Fetch entries
    r = list_entries()
    if r.status_code != 200:
        try:
            st.error(r.json().get("detail", "Could not load entries."))
        except requests.exceptions.JSONDecodeError:
            st.error(f"Server error: {r.text}")
        return

    raw_entries = r.json().get("entries", []) or []
    if not raw_entries:
        st.info("No journal entries yet — write something to get started!")
        return

    # Parse and attach datetime objects safely
    processed = []
    for e in raw_entries:
        created_raw = e.get("created_at") or ""
        try:
            dt = pd.to_datetime(created_raw)
            if pd.isna(dt):
                dt = None
        except Exception:
            dt = None
        processed.append({**e, "_dt": dt})

    # Sort entries by datetime descending (None last)
    processed.sort(key=lambda x: x["_dt"] if x["_dt"] is not None else pd.Timestamp.min, reverse=True)

    # Group by date (use date() from datetime) — None (unknown date) will be grouped under "Unknown date"
    def date_key(item):
        dt = item.get("_dt")
        if dt is None:
            return None
        return dt.date()

    grouped = []
    for key, group in groupby(processed, key=date_key):
        group_list = list(group)
        grouped.append((key, group_list))

    # Render grouped entries: each date as an expander
    for date_key, entries_for_date in grouped:
        if date_key is None:
            date_label = "Unknown Date"
        else:
            # Human-friendly date like "12 June 2025"
            date_label = date_key.strftime("%d %B %Y")

        expander_label = f"{date_label} — {len(entries_for_date)} entr{'y' if len(entries_for_date)==1 else 'ies'}"
        with st.expander(expander_label, expanded=False):
            # For each entry in that date, show title, time and content, with edit/delete
            for e in entries_for_date:
                e_id = e.get("id") or f"no-id-{hash(e.get('content',''))}"
                dt = e.get("_dt")
                time_str = dt.strftime("%I:%M %p") if dt is not None else "Unknown time"

                # Create a title from first line or truncate
                content = e.get("content", "") or ""
                first_line = content.splitlines()[0].strip() if content.splitlines() else ""
                title = first_line if first_line else (content[:60].strip() + ("..." if len(content) > 60 else ""))
                title = title or "Entry"

                # Header row: bold title + time on the right
                st.markdown(f"**{title}**  \n<small style='color:#475569;'> {time_str}</small>", unsafe_allow_html=True)

                # show full content (preserve newlines)
                st.write(content)

                # Mood / sentiment summary (if any)
                mood = e.get("mood_analysis") or {}
                if mood:
                    try:
                        sentiment = mood.get("sentiment", "unknown")
                        emotion = mood.get("emotion", "unknown")
                        score = mood.get("score", 0.0)
                        st.markdown(
                            f"**Sentiment:** <span style='font-weight:bold'>{sentiment}</span> — "
                            f"**Emotion:** <span style='font-weight:bold'>{emotion}</span> — "
                            f"**Score:** <span style='font-weight:bold'>{score:.2f}</span>",
                            unsafe_allow_html=True,
                        )
                    except Exception:
                        pass

                # Edit / Delete controls
                if st.session_state.get(f"edit_mode_{e_id}", False):
                    new_content = st.text_area("Edit entry", value=content, key=f"edit-area-{e_id}")
                    edit_col1, edit_col2 = st.columns(2)
                    with edit_col1:
                        if st.button("Save Edit", key=f"save-edit-{e_id}"):
                            er = edit_entry(e_id, new_content)
                            if er.status_code == 200:
                                st.success("Entry updated.")
                                # clear edit mode
                                if f"edit_mode_{e_id}" in st.session_state:
                                    del st.session_state[f"edit_mode_{e_id}"]
                                safe_rerun()
                            else:
                                st.error("Edit failed.")
                    with edit_col2:
                        if st.button("Cancel Edit", key=f"cancel-edit-{e_id}"):
                            if f"edit_mode_{e_id}" in st.session_state:
                                del st.session_state[f"edit_mode_{e_id}"]
                            safe_rerun()
                else:
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("Edit", key=f"edit-{e_id}"):
                            st.session_state[f"edit_mode_{e_id}"] = True
                            safe_rerun()
                    with col2:
                        if st.button("Delete", key=f"del-{e_id}"):
                            # ask server to delete
                            dr = delete_entry(e_id)
                            if dr.status_code in (200, 204):
                                st.success("Deleted.")
                            else:
                                try:
                                    st.error(dr.json().get("detail", "Delete failed."))
                                except Exception:
                                    st.error("Delete failed.")
                            safe_rerun()

                st.markdown("---")




def render_dashboard_page():
    if not st.session_state.get("token"):
        st.warning("Please log in to view the dashboard.")
        return

    st.markdown("<h1 style='color:#5A67D8;'>📊 Mood Trends</h1>", unsafe_allow_html=True)
    r = list_entries()
    if r.status_code != 200:
        try:
            st.error(r.json().get("detail", "Could not load dashboard data."))
        except requests.exceptions.JSONDecodeError:
            st.error(f"Server error: {r.text}")
        return

    entries = r.json().get("entries", [])
    if not entries:
        st.info("No mood data available. Write some journal entries first!")
        return
    
      # --- Build DataFrame ---
    rows = []
    for e in entries:
        mood = e.get("mood_analysis")
        if mood:
            rows.append({
                "date": pd.to_datetime(e["created_at"]),
                "emotion": mood.get("emotion", "Unknown").capitalize(),
                "sentiment": mood.get("sentiment", "Unknown"),
                "score": mood.get("score", 0.0),
                "recommendation": mood.get("recommendation", "")
            })
    df = pd.DataFrame(rows)
    if df.empty:
        st.info("No mood analysis data yet.")
        return
    
     # --- Latest mood & recommendation ---
    latest = df.sort_values("date", ascending=False).iloc[0]

    
    # ✅ Recommendation box
    if latest.get("recommendation"):
        st.markdown(
            f"""
            <div style="
                background:#75ba92;
                color:white;
                padding:1rem;
                border-radius:12px;
                margin:1rem 0;
                font-size:1.05rem;
                font-family:Poppins, sans-serif;
                box-shadow:0 3px 6px rgba(0,0,0,0.15);
            ">
                💡 <b>Recommendation:</b> {latest['recommendation']}
            </div>
            """,
            unsafe_allow_html=True
        )

    # rows = []
    # for e in entries:
    #     if e.get("mood_analysis"):
    #         rows.append({
    #             "date": pd.to_datetime(e["created_at"]),
    #             "emotion": e["mood_analysis"]["emotion"].capitalize(),
    #             "sentiment": e["mood_analysis"]["sentiment"],
    #             "score": e["mood_analysis"]["score"]
    #         })
    # df = pd.DataFrame(rows)
    # if df.empty:
    #     st.info("No mood analysis data yet.")
    #     return

    # --- Today’s mood ---
    latest = df.sort_values("date", ascending=False).iloc[0]
    st.markdown(
        f"""
        <h2 style='color:#48BB78;'>
            Today’s Mood: 
            <span style='font-size:0.85em; color:#2f855a; font-weight:600;'>
                {latest['emotion']} ({latest['sentiment']}, Score: {latest['score']:.2f})
            </span>
        </h2>
        """,
        unsafe_allow_html=True
    )

    # Set consistent color scheme
    color_scheme = alt.Scale(scheme="tableau10")
    

    # ================================
    # Weekly Mood Trend (Past 7 days)
    # ================================
    st.markdown("<h2 style='color:#5A67D8;'>Weekly Mood Trend</h2>", unsafe_allow_html=True)
    one_week_ago = datetime.now() - timedelta(days=7)
    df_week = df[df["date"] >= one_week_ago]

    if not df_week.empty:
        df_week["day"] = df_week["date"].dt.day_name()
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        weekly_stats = df_week.groupby(["day", "emotion"]).agg(
            count=("score", "size"),
            avg_score=("score", "mean")
        ).reset_index()

        # Ensure all days are included
        all_days = pd.DataFrame({"day": day_order})
        weekly_stats = all_days.merge(weekly_stats, on="day", how="left").fillna({"count": 0, "avg_score": 0})

        chart = (
            alt.Chart(weekly_stats)
            .mark_bar(size=40)
            .encode(
                x=alt.X("day:N", title="Day of Week", sort=day_order),
                y=alt.Y("count:Q", title="Mood Count"),
                color=alt.Color("emotion:N", scale=color_scheme),
                tooltip=["day", "emotion", "count", alt.Tooltip("avg_score:Q", format=".2f")]
            )
            .properties(width=700, height=300, title="Weekly Mood Counts & Scores")
            .configure_view(strokeWidth=0, fill="#F9FAFB")
        )
        st.altair_chart(chart, use_container_width=True)

    # ================================
    # Monthly Mood Distribution (Past 1 month)
    # ================================
    st.markdown("<h2 style='color:#5A67D8;'>Monthly Mood Distribution</h2>", unsafe_allow_html=True)
    one_month_ago = datetime.now() - timedelta(days=30)
    df_month = df[df["date"] >= one_month_ago]

    def week_label(day):
        if day <= 7: return "Week 1 (1–7)"
        elif day <= 14: return "Week 2 (8–14)"
        elif day <= 21: return "Week 3 (15–21)"
        elif day <= 28: return "Week 4 (22–28)"
        else: return "Week 5 (29–31)"

    week_order = ["Week 1 (1–7)", "Week 2 (8–14)", "Week 3 (15–21)", "Week 4 (22–28)", "Week 5 (29–31)"]

    if not df_month.empty:
        df_month["week_of_month"] = df_month["date"].dt.day.apply(week_label)
        month_stats = df_month.groupby(["week_of_month", "emotion"]).agg(
            count=("score", "size"),
            avg_score=("score", "mean")
        ).reset_index()

        # Ensure all weeks are included
        all_weeks = pd.DataFrame({"week_of_month": week_order})
        month_stats = all_weeks.merge(month_stats, on="week_of_month", how="left").fillna({"count": 0, "avg_score": 0})

        chart = (
            alt.Chart(month_stats)
            .mark_bar(size=40)
            .encode(
                x=alt.X("week_of_month:N", title="Week of Month", sort=week_order),
                y=alt.Y("count:Q", title="Mood Count"),
                color=alt.Color("emotion:N", scale=color_scheme),
                tooltip=["week_of_month", "emotion", "count", alt.Tooltip("avg_score:Q", format=".2f")]
            )
            .properties(width=700, height=300, title="Monthly Mood Counts & Scores")
            .configure_view(strokeWidth=0, fill="#F9FAFB")
        )
        st.altair_chart(chart, use_container_width=True)

    # ================================
    # Yearly Overall Emotion Distribution (Past 1 year)
    # ================================
    st.markdown("<h2 style='color:#5A67D8;'>Overall Emotion Distribution</h2>", unsafe_allow_html=True)
    one_year_ago = datetime.now() - timedelta(days=365)
    df_year = df[df["date"] >= one_year_ago]

    if not df_year.empty:
        pie_data = df_year["emotion"].value_counts().reset_index()
        pie_data.columns = ["emotion", "count"]

        pie_chart = (
            alt.Chart(pie_data)
            .mark_arc()
            .encode(
                theta="count:Q",
                color=alt.Color("emotion:N", scale=color_scheme),
                tooltip=["emotion", "count"]
            )
            .properties(width=500, height=400, title="Emotion Distribution (Past Year)")
            .configure_view(strokeWidth=0, fill="#F9FAFB")
        )
        st.altair_chart(pie_chart, use_container_width=True)



# --- Main ---
def main():
    st.set_page_config(page_title="AI Journal", layout="centered", page_icon="📝")

    
    # --- Modern CSS Theme ---
    st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
  :root{
    --primary-color: #5A67D8;
    --primary-color-dark: #4C51BF;
    --secondary-color: #48BB78;
    --accent-color: #F6AD55;
    --background-color: #F9FAFB;
    --text-color: #2D3748;
    --light-gray: #E2E8F0;
    --white: #FFFFFF;
    --button-width: 220px;
  }
  html, body, [class*="st-"], [class*="css-"]{
    font-family: 'Poppins', sans-serif;
    background-color: var(--background-color);
    color: var(--text-color);
  }
  section[data-testid="stSidebar"],
  div[data-testid="stSidebar"]{
    background-color: #dedede !important;
    border-right: 1px solid rgba(0,0,0,0.06);
  }
  section[data-testid="stSidebar"] *,
  div[data-testid="stSidebar"] * {
    color: #000000 !important;
    background-color: transparent !important;
  }
 /* Global solid indigo buttons */
.stButton>button,
div[data-testid="stFormSubmitButton"] button {
    width: var(--button-width) !important;
    display: inline-block !important;
    margin: 8px auto !important;
    padding: 10px 14px !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    text-align: center !important;

    background-color: var(--primary-color) !important;
    background-image: none !important;
    color: var(--white) !important;

    border: none !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    transition: transform .08s ease, box-shadow .08s ease, background-color .12s ease;
}
.stButton>button:hover,
div[data-testid="stFormSubmitButton"] button:hover {
    background-color: var(--primary-color-dark) !important;
    background-image: none !important;
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(90,103,216,0.15) !important;
}
.stButton>button:active,
div[data-testid="stFormSubmitButton"] button:active {
    transform: translateY(0);
    box-shadow: 0 3px 8px rgba(90,103,216,0.12) !important;
}
.stButton>button:focus,
div[data-testid="stFormSubmitButton"] button:focus {
    outline: none !important;
    box-shadow: 0 0 0 4px rgba(90,103,216,0.25) !important;
}


  section[data-testid="stSidebar"] .stButton>button,
  div[data-testid="stSidebar"] .stButton>button,
  section[data-testid="stSidebar"] button,
  div[data-testid="stSidebar"] button {
    width: var(--button-width) !important;
    box-sizing: border-box !important;
    display: block !important;
    margin: 10px auto !important;
    padding: 10px 12px !important;
    border-radius: 8px !important;
    background-color: var(--primary-color) !important;
    color: var(--white) !important;
    border: 1px solid rgba(0,0,0,0.06) !important;
    font-weight: 600 !important;
    text-align: center !important;
  }
  section[data-testid="stSidebar"] .stButton>button:hover,
  div[data-testid="stSidebar"] .stButton>button:hover,
  section[data-testid="stSidebar"] button:hover,
  div[data-testid="stSidebar"] button:hover {
    background-color: var(--primary-color-dark) !important;
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(90,103,216,0.08) !important;
  }
  .main .block-container{
    background: transparent !important;
  }
  input, textarea, select{
    border-radius: 0.5rem !important;
    border: 1px solid var(--light-gray) !important;
    padding: 0.45rem !important;
    color: #111827 !important;
  }
  input:focus, textarea:focus{
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 6px rgba(90,103,216,0.06) !important;
  }
  @media (max-width: 520px) {
    :root { --button-width: 100% !important; }
    .stButton>button, section[data-testid="stSidebar"] .stButton>button {
      width: 100% !important;
      margin-left: 0 !important;
      margin-right: 0 !important;
    }
  }
  div[data-testid="stNotification"] {
    background-color: var(--secondary-color) !important;
    border-left: 4px solid var(--secondary-color) !important;
  }
  div[data-testid="stNotification"] p {
    color: var(--secondary-color) !important;
    font-weight: 500 !important;
  }
  div[data-testid="stNotification"] .stButton>button {
    background-color: var(--secondary-color) !important;
    border-color: var(--secondary-color) !important;
    color: var(--secondary-color) !important;
    background-image: none !important;
  }
  div[data-testid="stNotification"] .stButton>button:hover {
    background-color: #3fa86a !important;
    box-shadow: 0 6px 18px rgba(72,187,120,0.08) !important;
  }
</style>
    """, unsafe_allow_html=True)

    st.markdown(
        "<h1 style='color:#5A67D8;font-family:Poppins,sans-serif;text-align:center;'>AI-Powered Personal Journal</h1>", 
        unsafe_allow_html=True
    )




    initialize_session_state()
    render_sidebar()

    page = st.session_state.page
    if page == "home": render_home_page()
    elif page == "register": render_register_page()
    elif page == "verify": render_verify_page()
    elif page == "login": render_login_page()
    elif page == "journal": render_journal_page()
    elif page == "dashboard": render_dashboard_page()
    else:
        st.session_state.page = "home"
        safe_rerun()

if __name__ == "__main__":
    main()