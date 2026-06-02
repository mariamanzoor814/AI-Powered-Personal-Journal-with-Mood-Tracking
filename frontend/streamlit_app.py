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
        st.markdown("<div style='margin-bottom:30px'></div>", unsafe_allow_html=True)
        
        # Logo/Title
        st.markdown(
            """
            <div style='text-align:center; margin-bottom:30px;'>
                <h2 style='color:#5B4FB3; margin:0; font-size:1.8rem;'>📓 MindJournal</h2>
                <p style='color:#999; margin-top:5px; font-size:0.9rem;'>Your AI-Powered Reflection</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("---")
        
        if st.session_state.get("token"):
            st.markdown(f"<p style='color:#666; font-size:0.9rem; margin-bottom:20px;'>Welcome, {st.session_state.get('username', 'User')}</p>", unsafe_allow_html=True)
            
            # Navigation buttons
            nav_cols = st.columns(1)
            
            if st.button("📔 My Journal", key="sidebar-journal", use_container_width=True):
                st.session_state.page = "journal"
                safe_rerun()
            
            if st.button("📊 Dashboard", key="sidebar-dashboard", use_container_width=True):
                st.session_state.page = "dashboard"
                safe_rerun()
            
            st.markdown("---")
            
            if st.button("🚪 Logout", key="sidebar-logout", use_container_width=True):
                clear_token()
                st.session_state.username = None
                st.session_state.page = "home"
                st.success("Logged out successfully.")
                safe_rerun()
        else:
            if st.button("🏠 Home", key="sidebar-home", use_container_width=True):
                st.session_state.page = "home"
                safe_rerun()
            
            if st.button("✍️ Register", key="sidebar-register", use_container_width=True):
                st.session_state.page = "register"
                safe_rerun()
            
            if st.button("🔓 Login", key="sidebar-login", use_container_width=True):
                st.session_state.page = "login"
                safe_rerun()

def render_home_page():
    st.markdown(
        """
        <div style='text-align:center; margin:3rem 0 2rem 0;'>
            <h1 style='font-size:3rem; color:#5B4FB3; margin:0; font-weight:700;'>Welcome to MindJournal</h1>
            <p style='font-size:1.1rem; color:#666; margin-top:1rem; line-height:1.6;'>
                Discover your emotions, understand your patterns, transform your well-being
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("<div style='margin:3rem 0;'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3, gap="medium")
    
    with col1:
        st.markdown(
            """
            <div style='
                background: linear-gradient(135deg, #f5f3ff 0%, #f0e8ff 100%);
                border: 1px solid #e8dff5;
                border-radius: 16px;
                padding: 2rem;
                text-align: center;
                height: 100%;
                box-shadow: 0 2px 8px rgba(91, 79, 179, 0.08);
                transition: transform 0.3s ease;
            '>
                <div style='font-size: 2.5rem; margin-bottom: 1rem;'>😊</div>
                <h3 style='color: #5B4FB3; margin: 0 0 0.5rem 0;'>AI Mood Analysis</h3>
                <p style='color: #666; font-size: 0.95rem; margin: 0;'>
                    Automatic sentiment and emotion detection powered by advanced AI
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            """
            <div style='
                background: linear-gradient(135deg, #f0faf8 0%, #e6f5f2 100%);
                border: 1px solid #d4ebe6;
                border-radius: 16px;
                padding: 2rem;
                text-align: center;
                height: 100%;
                box-shadow: 0 2px 8px rgba(76, 175, 80, 0.08);
                transition: transform 0.3s ease;
            '>
                <div style='font-size: 2.5rem; margin-bottom: 1rem;'>📊</div>
                <h3 style='color: #4CAF50; margin: 0 0 0.5rem 0;'>Rich Analytics</h3>
                <p style='color: #666; font-size: 0.95rem; margin: 0;'>
                    Visualize your mood patterns across days, weeks, and months
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            """
            <div style='
                background: linear-gradient(135deg, #fff5f0 0%, #ffe6db 100%);
                border: 1px solid #ffd9cc;
                border-radius: 16px;
                padding: 2rem;
                text-align: center;
                height: 100%;
                box-shadow: 0 2px 8px rgba(255, 107, 53, 0.08);
                transition: transform 0.3s ease;
            '>
                <div style='font-size: 2.5rem; margin-bottom: 1rem;'>💡</div>
                <h3 style='color: #FF6B35; margin: 0 0 0.5rem 0;'>Smart Insights</h3>
                <p style='color: #666; font-size: 0.95rem; margin: 0;'>
                    Receive personalized recommendations for mental well-being
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown("<div style='margin:2rem 0;'></div>", unsafe_allow_html=True)
    
    col_btn = st.columns([1, 2, 1])
    with col_btn[1]:
        if st.button("🚀 Get Started", key="cta-btn", use_container_width=True):
            st.session_state.page = "login"
            safe_rerun()

def render_register_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            """
            <div style='text-align:center; margin-bottom:2rem;'>
                <h2 style='color:#5B4FB3; margin:0; font-size:2rem;'>Create Account</h2>
                <p style='color:#999; margin-top:0.5rem;'>Join our community of mindful journalers</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        with st.form("register_form"):
            username = st.text_input("👤 Username", placeholder="Choose a unique username", label_visibility="visible")
            email = st.text_input("📧 Email", placeholder="your.email@example.com", label_visibility="visible")
            password = st.text_input("🔐 Password", type="password", placeholder="Create a strong password", label_visibility="visible")
            submitted = st.form_submit_button("Create Account", use_container_width=True)

            if submitted:
                r = post_register(username, email, password)
                if r.status_code == 201:
                    st.success("✅ Registration successful! Check your email for verification code.")
                    st.session_state.email_for_verification = email
                    st.session_state.page = "verify"
                    safe_rerun()
                else:
                    try:
                        st.error(r.json().get("detail", "Registration failed. Please try again."))
                    except requests.exceptions.JSONDecodeError:
                        st.error(f"Server error: {r.text}")
        
        st.markdown(
            """
            <div style='text-align:center; margin-top:1.5rem;'>
                <p style='color:#666;'>Already have an account? 
                <a href='#' onclick='window.location.reload()' style='color:#5B4FB3; text-decoration:none; font-weight:600;'>Sign in here</a></p>
            </div>
            """,
            unsafe_allow_html=True
        )

def render_verify_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            """
            <div style='text-align:center; margin-bottom:2rem;'>
                <h2 style='color:#5B4FB3; margin:0; font-size:2rem;'>Verify Your Account</h2>
                <p style='color:#999; margin-top:0.5rem;'>Enter the verification code sent to your email</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        email = st.text_input("📧 Email", value=st.session_state.get("email_for_verification", ""), disabled=True, label_visibility="visible")
        otp = st.text_input("🔑 Verification Code", placeholder="Enter 6-digit code", label_visibility="visible")

        if st.button("Verify Account", use_container_width=True):
            r = post_verify(email, otp)
            if r.status_code == 200:
                st.success("✅ Account verified successfully! Redirecting to login...")
                st.session_state.page = "login"
                st.balloons()
                safe_rerun()
            else:
                try:
                    st.error(r.json().get("detail", "Verification failed. Check the code and try again."))
                except requests.exceptions.JSONDecodeError:
                    st.error(f"Server error: {r.text}")

def render_login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            """
            <div style='text-align:center; margin-bottom:2rem;'>
                <h2 style='color:#5B4FB3; margin:0; font-size:2rem;'>Welcome Back</h2>
                <p style='color:#999; margin-top:0.5rem;'>Sign in to access your journal</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        with st.form("login_form"):
            email = st.text_input("📧 Email", placeholder="your.email@example.com", label_visibility="visible")
            password = st.text_input("🔐 Password", type="password", placeholder="Enter your password", label_visibility="visible")
            remember_me = st.checkbox("Remember me on this device")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

            if submitted:
                r = post_login(email, password)
                if r.status_code == 200:
                    token = r.json().get("access_token")
                    st.session_state.token = token
                    st.session_state.username = email
                    save_token(token, username=email, remember=remember_me)
                    st.session_state.page = "journal"
                    st.success("✅ Logged in successfully!")
                    safe_rerun()
                else:
                    try:
                        st.error(r.json().get("detail", "Login failed. Check your credentials."))
                    except requests.exceptions.JSONDecodeError:
                        st.error(f"Server error: {r.text}")
        
        st.markdown(
            """
            <div style='text-align:center; margin-top:1.5rem;'>
                <p style='color:#666;'>Don't have an account? 
                <a href='#' onclick='window.location.reload()' style='color:#5B4FB3; text-decoration:none; font-weight:600;'>Sign up here</a></p>
            </div>
            """,
            unsafe_allow_html=True
        )

def render_journal_page():
    if not st.session_state.get("token"):
        st.warning("Please log in to access your journal.")
        return

    # Header
    st.markdown(
        """
        <div style='margin-bottom: 2rem;'>
            <h1 style='color:#5B4FB3; margin:0 0 0.5rem 0; font-size:2.5rem;'>📔 My Journal</h1>
            <p style='color:#999; margin:0;'>Write, reflect, and understand yourself better</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # New Entry Section
    st.markdown(
        """
        <div style='
            background: linear-gradient(135deg, #f5f3ff 0%, #f0e8ff 100%);
            border: 2px dashed #d4c5f0;
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
        '>
            <h3 style='color:#5B4FB3; margin:0 0 1rem 0;'>✨ Write a New Entry</h3>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    text = st.text_area("What's on your mind?", height=180, key="journal_text_area", placeholder="Share your thoughts, feelings, and experiences...")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if st.button("💾 Save Entry", key="save-entry-btn", use_container_width=True):
            if text.strip():
                r = create_entry(text)
                if r.status_code in [200, 201]:
                    st.success("✅ Entry saved successfully!")
                    safe_rerun()
                else:
                    try:
                        st.error(r.json().get("detail", "Failed to save entry."))
                    except requests.exceptions.JSONDecodeError:
                        st.error(f"Server error: {r.text}")
            else:
                st.warning("Please write something before saving.")

    st.markdown("---")
    
    # Entries List
    st.markdown(
        """
        <div style='margin: 2rem 0 1rem 0;'>
            <h2 style='color:#5B4FB3; margin:0; font-size:1.8rem;'>📚 Your Entries</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

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
        st.info("📝 No entries yet — start writing to begin your journey!")
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

    # Group by date
    def date_key(item):
        dt = item.get("_dt")
        if dt is None:
            return None
        return dt.date()

    grouped = []
    for key, group in groupby(processed, key=date_key):
        group_list = list(group)
        grouped.append((key, group_list))

    # Render grouped entries
    for date_key, entries_for_date in grouped:
        if date_key is None:
            date_label = "Unknown Date"
        else:
            date_label = date_key.strftime("%d %B %Y")

        expander_label = f"{date_label} — {len(entries_for_date)} entr{'y' if len(entries_for_date)==1 else 'ies'}"
        with st.expander(expander_label, expanded=True):
            for e in entries_for_date:
                e_id = e.get("id") or f"no-id-{hash(e.get('content',''))}"
                dt = e.get("_dt")
                time_str = dt.strftime("%I:%M %p") if dt is not None else "Unknown time"
                content = e.get("content", "") or ""

                # Get mood analysis
                mood = e.get("mood_analysis") or {}
                sentiment = mood.get("sentiment", "Unknown")
                emotion = mood.get("emotion", "Unknown")
                score = mood.get("score", 0.0)

                # Entry Card
                st.markdown(
                    f"""
                    <div style='
                        background: #ffffff;
                        border: 1px solid #e8e8e8;
                        border-radius: 12px;
                        padding: 1.5rem;
                        margin-bottom: 1rem;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                    '>
                        <div style='display:flex; justify-content:space-between; align-items:start; margin-bottom:1rem;'>
                            <div>
                                <h3 style='color:#5B4FB3; margin:0; font-size:1.5rem;'>{emotion}</h3>
                                <p style='color:#999; margin:0.3rem 0 0 0; font-size:0.9rem;'>{time_str}</p>
                            </div>
                            <div style='text-align:right;'>
                                <p style='color:#666; margin:0; font-size:0.85rem;'><strong>Confidence:</strong> {score:.0%}</p>
                            </div>
                        </div>
                        
                        <div style='
                            background: #f8f8f8;
                            border-left: 3px solid #5B4FB3;
                            padding: 1rem;
                            border-radius: 6px;
                            margin-bottom: 1rem;
                        '>
                            <p style='color:#333; margin:0; line-height:1.6; font-size:1rem;'>{content}</p>
                        </div>
                        
                        <div style='
                            background: linear-gradient(90deg, #f5f3ff 0%, #f0e8ff 100%);
                            padding: 0.75rem 1rem;
                            border-radius: 8px;
                            margin-bottom: 1rem;
                            display:flex; gap:1rem; flex-wrap:wrap;
                        '>
                            <span style='color:#666;'><strong>Sentiment:</strong> <span style='color:#5B4FB3;'>{sentiment}</span></span>
                            <span style='color:#666;'><strong>Mood:</strong> <span style='color:#5B4FB3;'>{emotion}</span></span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Edit / Delete controls
                if st.session_state.get(f"edit_mode_{e_id}", False):
                    st.markdown("<p style='color:#5B4FB3; font-weight:600; margin-bottom:0.5rem;'>✏️ Edit Entry</p>", unsafe_allow_html=True)
                    new_content = st.text_area("Edit your entry", value=content, key=f"edit-area-{e_id}", height=150)
                    edit_col1, edit_col2 = st.columns(2)
                    with edit_col1:
                        if st.button("✅ Save Changes", key=f"save-edit-{e_id}", use_container_width=True):
                            er = edit_entry(e_id, new_content)
                            if er.status_code == 200:
                                st.success("Entry updated!")
                                if f"edit_mode_{e_id}" in st.session_state:
                                    del st.session_state[f"edit_mode_{e_id}"]
                                safe_rerun()
                            else:
                                st.error("Edit failed.")
                    with edit_col2:
                        if st.button("❌ Cancel", key=f"cancel-edit-{e_id}", use_container_width=True):
                            if f"edit_mode_{e_id}" in st.session_state:
                                del st.session_state[f"edit_mode_{e_id}"]
                            safe_rerun()
                else:
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✏️ Edit", key=f"edit-{e_id}", use_container_width=True):
                            st.session_state[f"edit_mode_{e_id}"] = True
                            safe_rerun()
                    with col2:
                        if st.button("🗑️ Delete", key=f"del-{e_id}", use_container_width=True):
                            dr = delete_entry(e_id)
                            if dr.status_code in (200, 204):
                                st.success("Entry deleted.")
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

    st.markdown(
        """
        <div style='margin-bottom: 2rem;'>
            <h1 style='color:#5B4FB3; margin:0 0 0.5rem 0; font-size:2.5rem;'>📊 Mood Insights</h1>
            <p style='color:#999; margin:0;'>Visualize your emotional patterns and progress</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    r = list_entries()
    if r.status_code != 200:
        try:
            st.error(r.json().get("detail", "Could not load dashboard data."))
        except requests.exceptions.JSONDecodeError:
            st.error(f"Server error: {r.text}")
        return

    entries = r.json().get("entries", [])
    if not entries:
        st.info("📝 No mood data yet. Write some journal entries to see your insights!")
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
                background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                color: white;
                padding: 1.5rem;
                border-radius: 12px;
                margin: 1.5rem 0;
                font-size: 1.05rem;
                font-family: 'Segoe UI', sans-serif;
                box-shadow: 0 4px 12px rgba(76, 175, 80, 0.25);
            ">
                <div style='display:flex; align-items:center; gap:1rem;'>
                    <span style='font-size:1.8rem;'>💡</span>
                    <div>
                        <p style='margin:0; font-weight:600; margin-bottom:0.3rem;'>Today's Insight</p>
                        <p style='margin:0;'>{latest['recommendation']}</p>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # --- Today's mood card ---
    st.markdown(
        f"""
        <div style='
            background: linear-gradient(135deg, #5B4FB3 0%, #7c6fd4 100%);
            color: white;
            padding: 2rem;
            border-radius: 16px;
            margin: 2rem 0;
            box-shadow: 0 4px 12px rgba(91, 79, 179, 0.25);
        '>
            <p style='margin:0 0 0.5rem 0; font-size:0.95rem; opacity:0.9;'>TODAY'S MOOD</p>
            <h2 style='margin:0; font-size:2.5rem; font-weight:700;'>{latest['emotion']}</h2>
            <p style='margin:0.5rem 0 0 0; font-size:0.95rem; opacity:0.95;'>
                Sentiment: <strong>{latest['sentiment']}</strong> • Confidence: <strong>{latest['score']:.0%}</strong>
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Set consistent color scheme
    color_scheme = alt.Scale(scheme="tableau10")
    
    # ================================
    # Weekly Mood Trend (Past 7 days)
    # ================================
    st.markdown(
        "<h2 style='color:#5B4FB3; margin-top:2rem;'>Weekly Mood Trend</h2>",
        unsafe_allow_html=True
    )
    one_week_ago = datetime.now() - timedelta(days=7)
    df_week = df[df["date"] >= one_week_ago]

    if not df_week.empty:
        df_week["day"] = df_week["date"].dt.day_name()
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        weekly_stats = df_week.groupby(["day", "emotion"]).agg(
            count=("score", "size"),
            avg_score=("score", "mean")
        ).reset_index()

        all_days = pd.DataFrame({"day": day_order})
        weekly_stats = all_days.merge(weekly_stats, on="day", how="left").fillna({"count": 0, "avg_score": 0})

        chart = (
            alt.Chart(weekly_stats)
            .mark_bar(size=40, cornerRadius=8)
            .encode(
                x=alt.X("day:N", title="Day of Week", sort=day_order),
                y=alt.Y("count:Q", title="Mood Count"),
                color=alt.Color("emotion:N", scale=color_scheme),
                tooltip=["day", "emotion", "count", alt.Tooltip("avg_score:Q", format=".2f")]
            )
            .properties(width=700, height=300)
            .configure_view(strokeWidth=0, fill="transparent")
            .configure_axis(grid=True, gridOpacity=0.1)
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No mood data for this week yet.")

    # ================================
    # Monthly Mood Distribution
    # ================================
    st.markdown(
        "<h2 style='color:#5B4FB3; margin-top:2rem;'>Monthly Mood Distribution</h2>",
        unsafe_allow_html=True
    )
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

        all_weeks = pd.DataFrame({"week_of_month": week_order})
        month_stats = all_weeks.merge(month_stats, on="week_of_month", how="left").fillna({"count": 0, "avg_score": 0})

        chart = (
            alt.Chart(month_stats)
            .mark_bar(size=40, cornerRadius=8)
            .encode(
                x=alt.X("week_of_month:N", title="Week of Month", sort=week_order),
                y=alt.Y("count:Q", title="Mood Count"),
                color=alt.Color("emotion:N", scale=color_scheme),
                tooltip=["week_of_month", "emotion", "count", alt.Tooltip("avg_score:Q", format=".2f")]
            )
            .properties(width=700, height=300)
            .configure_view(strokeWidth=0, fill="transparent")
            .configure_axis(grid=True, gridOpacity=0.1)
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No mood data for this month yet.")

    # ================================
    # Overall Emotion Distribution
    # ================================
    st.markdown(
        "<h2 style='color:#5B4FB3; margin-top:2rem;'>Overall Emotion Distribution</h2>",
        unsafe_allow_html=True
    )
    one_year_ago = datetime.now() - timedelta(days=365)
    df_year = df[df["date"] >= one_year_ago]

    if not df_year.empty:
        pie_data = df_year["emotion"].value_counts().reset_index()
        pie_data.columns = ["emotion", "count"]

        pie_chart = (
            alt.Chart(pie_data)
            .mark_arc(innerRadius=50, cornerRadius=6)
            .encode(
                theta="count:Q",
                color=alt.Color("emotion:N", scale=color_scheme),
                tooltip=["emotion", "count"]
            )
            .properties(width=500, height=400)
            .configure_view(strokeWidth=0, fill="transparent")
        )
        st.altair_chart(pie_chart, use_container_width=True)
    else:
        st.info("No mood data available yet.")


# --- Main ---
def main():
    st.set_page_config(page_title="MindJournal - AI-Powered Personal Journal", layout="wide", page_icon="📓", initial_sidebar_state="expanded")

    # --- Modern Notion-like CSS Theme ---
    st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  :root {
    --primary-color: #5B4FB3;
    --primary-light: #7c6fd4;
    --primary-dark: #4a3d8a;
    --secondary-color: #4CAF50;
    --accent-color: #FF6B35;
    --background-color: #ffffff;
    --surface-color: #f8f9fa;
    --border-color: #e8e8e8;
    --text-primary: #333333;
    --text-secondary: #666666;
    --text-tertiary: #999999;
  }

  /* Base styles */
  .stApp, html, body {
    background-color: var(--background-color) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
  }

  .main .block-container {
    max-width: 1400px;
    padding: 2rem 2rem !important;
  }

  /* Sidebar */
  section[data-testid="stSidebar"],
  div[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    border-right: 1px solid var(--border-color) !important;
  }

  section[data-testid="stSidebar"] *,
  div[data-testid="stSidebar"] * {
    color: var(--text-primary) !important;
  }

  /* Sidebar buttons */
  section[data-testid="stSidebar"] .stButton>button,
  div[data-testid="stSidebar"] .stButton>button {
    background-color: var(--surface-color) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 10px !important;
    padding: 0.75rem 1rem !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    margin-bottom: 0.5rem !important;
  }

  section[data-testid="stSidebar"] .stButton>button:hover,
  div[data-testid="stSidebar"] .stButton>button:hover {
    background-color: var(--primary-color) !important;
    color: white !important;
    border-color: var(--primary-color) !important;
  }

  /* Form container */
  .stForm {
    background: var(--background-color) !important;
    padding: 2rem !important;
    border-radius: 16px !important;
    border: 1px solid var(--border-color) !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
    margin: 1rem auto !important;
    max-width: 500px !important;
  }

  /* Input fields */
  input[type="text"],
  input[type="password"],
  input[type="email"],
  textarea,
  .stTextInput>div>input,
  .stPasswordInput>div>input,
  .stTextArea>div>textarea {
    background: var(--surface-color) !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-primary) !important;
    border-radius: 10px !important;
    padding: 0.75rem 1rem !important;
    font-size: 0.95rem !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.2s ease !important;
  }

  input:focus,
  textarea:focus {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 3px rgba(91, 79, 179, 0.1) !important;
    outline: none !important;
  }

  /* Labels */
  label,
  .stTextInput label,
  .stPasswordInput label,
  .stTextArea label {
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
    margin-bottom: 0.5rem !important;
  }

  /* Buttons */
  .stButton>button,
  button[kind="primary"],
  div[data-testid="stFormSubmitButton"] button {
    background-color: var(--primary-color) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.75rem 1.5rem !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
  }

  .stButton>button:hover,
  button[kind="primary"]:hover,
  div[data-testid="stFormSubmitButton"] button:hover {
    background-color: var(--primary-dark) !important;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(91, 79, 179, 0.3) !important;
  }

  /* Checkbox */
  .stCheckbox input[type="checkbox"] {
    accent-color: var(--primary-color) !important;
  }

  .stCheckbox label {
    font-weight: 500 !important;
    color: var(--text-primary) !important;
  }

  /* Headings */
  h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary) !important;
    font-weight: 700 !important;
    letter-spacing: -0.5px;
  }

  /* Messages */
  .stSuccess, .stError, .stWarning, .stInfo {
    border-radius: 12px !important;
    padding: 1rem !important;
    margin: 1rem 0 !important;
  }

  .stSuccess {
    background-color: rgba(76, 175, 80, 0.1) !important;
    border: 1px solid rgba(76, 175, 80, 0.3) !important;
    color: #2e7d32 !important;
  }

  .stError {
    background-color: rgba(244, 67, 54, 0.1) !important;
    border: 1px solid rgba(244, 67, 54, 0.3) !important;
    color: #c62828 !important;
  }

  .stWarning {
    background-color: rgba(255, 107, 53, 0.1) !important;
    border: 1px solid rgba(255, 107, 53, 0.3) !important;
    color: #d84315 !important;
  }

  .stInfo {
    background-color: rgba(91, 79, 179, 0.1) !important;
    border: 1px solid rgba(91, 79, 179, 0.3) !important;
    color: #4a3d8a !important;
  }

  /* Expander */
  .streamlit-expanderHeader {
    background-color: var(--surface-color) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
  }

  .streamlit-expanderHeader:hover {
    background-color: #f0e8ff !important;
  }

  /* Divider */
  hr {
    border: none !important;
    height: 1px !important;
    background-color: var(--border-color) !important;
    margin: 2rem 0 !important;
  }

  /* Column layout */
  .stColumns {
    gap: 1.5rem !important;
  }

</style>
    """, unsafe_allow_html=True)

    st.markdown(
        "<h1 style='color:#5B4FB3; font-family:Inter, sans-serif; text-align:center; margin-bottom:2rem; display:none;'>📓 MindJournal</h1>", 
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
