import os
import streamlit as st
import requests
import pandas as pd
import altair as alt
from itertools import groupby
from datetime import datetime, timedelta
import json


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

# --- MODERN ANIMATED LANDING PAGE ---
def render_home_page():
    st.markdown(
        """
        <style>
            @keyframes fadeInDown {
                from { opacity: 0; transform: translateY(-30px); } to { opacity: 1; transform: translateY(0); }
            }
            @keyframes fadeInUp {
                from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); }
            }
            @keyframes slideInLeft {
                from { opacity: 0; transform: translateX(-50px); } to { opacity: 1; transform: translateX(0); }
            }
            @keyframes slideInRight {
                from { opacity: 0; transform: translateX(50px); } to { opacity: 1; transform: translateX(0); }
            }
            @keyframes float {
                0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-20px); }
            }
            @keyframes glow {
                0%, 100% { box-shadow: 0 0 20px rgba(147, 112, 219, 0.3); }
                50% { box-shadow: 0 0 40px rgba(147, 112, 219, 0.6); }
            }
            @keyframes rotateCard {
                0% { transform: rotateY(0deg); } 100% { transform: rotateY(360deg); }
            }
            
            .hero-wrapper {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
                border-radius: 30px;
                padding: 5rem 2rem;
                margin: 2rem 0;
                position: relative;
                overflow: hidden;
                box-shadow: 0 20px 60px rgba(102, 126, 234, 0.4);
                animation: fadeInDown 1s ease-out;
            }
            
            .hero-wrapper::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: radial-gradient(circle at 20% 50%, rgba(255,255,255,0.15) 0%, transparent 50%),
                            radial-gradient(circle at 80% 80%, rgba(255,255,255,0.1) 0%, transparent 50%);
                animation: glow 3s ease-in-out infinite;
            }
            
            .hero-title {
                font-size: 3.5rem;
                font-weight: 900;
                color: white;
                margin: 0;
                position: relative;
                z-index: 1;
                animation: fadeInDown 1.2s ease-out;
                text-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            
            .hero-subtitle {
                font-size: 1.2rem;
                color: rgba(255,255,255,0.95);
                margin-top: 1rem;
                position: relative;
                z-index: 1;
                animation: fadeInUp 1.2s ease-out;
            }
            
            .feature-card-home {
                background: white;
                border-radius: 20px;
                padding: 2.5rem;
                box-shadow: 0 10px 40px rgba(0,0,0,0.08);
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                border: 2px solid transparent;
                animation: fadeInUp 0.8s ease-out backwards;
                position: relative;
                overflow: hidden;
            }
            
            .feature-card-home:nth-child(1) { animation-delay: 0.1s; }
            .feature-card-home:nth-child(2) { animation-delay: 0.2s; }
            .feature-card-home:nth-child(3) { animation-delay: 0.3s; }
            
            .feature-card-home:hover {
                transform: translateY(-20px) scale(1.02);
                box-shadow: 0 30px 60px rgba(102, 126, 234, 0.25);
                border-color: #9370DB;
            }
            
            .feature-icon-home {
                font-size: 3.5rem;
                margin-bottom: 1rem;
                animation: float 3s ease-in-out infinite;
            }
            
            .feature-card-home:nth-child(2) .feature-icon-home { animation-delay: -1s; }
            .feature-card-home:nth-child(3) .feature-icon-home { animation-delay: -2s; }
            
            .feature-title-home {
                font-size: 1.3rem;
                font-weight: 700;
                color: #333;
                margin: 0 0 0.5rem 0;
            }
            
            .feature-desc-home {
                color: #666;
                font-size: 0.95rem;
                line-height: 1.6;
                margin: 0;
            }
            
            .cta-button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 50px;
                padding: 1rem 2.5rem;
                font-size: 1.1rem;
                font-weight: 700;
                cursor: pointer;
                box-shadow: 0 15px 35px rgba(102, 126, 234, 0.3);
                transition: all 0.3s ease;
                animation: fadeInUp 1.4s ease-out;
                margin-top: 2rem;
            }
            
            .cta-button:hover {
                transform: translateY(-5px);
                box-shadow: 0 25px 50px rgba(102, 126, 234, 0.4);
            }
        </style>
        
        <div class="hero-wrapper">
            <h1 class="hero-title">✨ MindFlow</h1>
            <p class="hero-subtitle">
                Discover your emotions, understand your patterns, transform your well-being.<br>
                Your AI-powered personal journal that listens, analyzes, and inspires.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Features
    col1, col2, col3 = st.columns(3, gap="large")
    
    with col1:
        st.markdown(
            """
            <div class="feature-card-home">
                <div class="feature-icon-home">🧠</div>
                <div class="feature-title-home">Smart Analysis</div>
                <div class="feature-desc-home">
                    AI-powered sentiment & emotion detection powered by advanced NLP models.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            """
            <div class="feature-card-home">
                <div class="feature-icon-home">📈</div>
                <div class="feature-title-home">Beautiful Insights</div>
                <div class="feature-desc-home">
                    Visualize your mood trends with stunning interactive charts and analytics.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            """
            <div class="feature-card-home">
                <div class="feature-icon-home">💪</div>
                <div class="feature-title-home">Personal Growth</div>
                <div class="feature-desc-home">
                    Receive AI-powered recommendations tailored to your emotional well-being.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    col_btn = st.columns([1, 2, 1])
    with col_btn[1]:
        if st.button("🚀 Get Started", key="cta-home", use_container_width=True):
            st.session_state.page = "register"
            safe_rerun()

# --- SIDEBAR NAVIGATION ---
def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div style='
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 15px;
                padding: 1.5rem;
                margin-bottom: 2rem;
                text-align: center;
                color: white;
            '>
                <div style='font-size: 2rem;'>✨</div>
                <h2 style='margin: 0.5rem 0 0 0; font-size: 1.5rem;'>MindFlow</h2>
                <p style='margin: 0.3rem 0 0 0; font-size: 0.85rem; opacity: 0.9;'>Your Digital Therapist</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("---")
        
        if st.session_state.get("token"):
            st.markdown(
                f"<p style='text-align: center; color: #667eea; font-weight: 600; margin-bottom: 1.5rem;'>👋 Welcome!</p>",
                unsafe_allow_html=True
            )
            
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
                st.balloons()
                safe_rerun()
        else:
            if st.button("📝 Sign In", key="sidebar-login", use_container_width=True):
                st.session_state.page = "login"
                safe_rerun()
            
            if st.button("✍️ Register", key="sidebar-register", use_container_width=True):
                st.session_state.page = "register"
                safe_rerun()

# --- AUTH PAGES ---
def render_register_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            """
            <style>
                .auth-card {
                    background: white;
                    border-radius: 20px;
                    padding: 2.5rem;
                    box-shadow: 0 20px 60px rgba(102, 126, 234, 0.15);
                    border: 1px solid rgba(102, 126, 234, 0.1);
                    animation: slideInRight 0.6s ease-out;
                }
                
                .auth-title {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    font-size: 2rem;
                    font-weight: 800;
                    margin: 0 0 0.5rem 0;
                }
                
                .auth-subtitle {
                    color: #999;
                    margin: 0 0 2rem 0;
                    font-size: 0.95rem;
                }
            </style>
            
            <div class="auth-card">
                <h2 class="auth-title">Create Account</h2>
                <p class="auth-subtitle">Join 10K+ mindful journalers</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        with st.form("register_form"):
            username = st.text_input("👤 Username", placeholder="Choose your username")
            email = st.text_input("📧 Email", placeholder="your.email@example.com")
            password = st.text_input("🔐 Password", type="password", placeholder="Create a strong password")
            submitted = st.form_submit_button("Create Account", use_container_width=True)

            if submitted:
                r = post_register(username, email, password)
                if r.status_code == 201:
                    st.success("✅ Check your email for verification code!")
                    st.session_state.email_for_verification = email
                    st.session_state.page = "verify"
                    safe_rerun()
                else:
                    try:
                        st.error(r.json().get("detail", "Registration failed."))
                    except:
                        st.error(f"Error: {r.text}")

def render_verify_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            """
            <div class="auth-card">
                <h2 class="auth-title">Verify Account</h2>
                <p class="auth-subtitle">Enter the code we sent to your email</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        email = st.text_input("📧 Email", value=st.session_state.get("email_for_verification", ""), disabled=True)
        otp = st.text_input("🔑 Verification Code", placeholder="6-digit code")

        if st.button("Verify", use_container_width=True):
            r = post_verify(email, otp)
            if r.status_code == 200:
                st.success("✅ Account verified!")
                st.session_state.page = "login"
                st.balloons()
                safe_rerun()
            else:
                st.error("Invalid or expired code")

def render_login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            """
            <div class="auth-card">
                <h2 class="auth-title">Welcome Back</h2>
                <p class="auth-subtitle">Sign in to your MindFlow account</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        with st.form("login_form"):
            email = st.text_input("📧 Email", placeholder="your.email@example.com")
            password = st.text_input("🔐 Password", type="password", placeholder="Enter your password")
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
                    st.balloons()
                    safe_rerun()
                else:
                    st.error("Invalid email or password")

# --- JOURNAL PAGE ---
def render_journal_page():
    if not st.session_state.get("token"):
        st.warning("Please log in to access your journal.")
        return

    st.markdown(
        """
        <style>
            .journal-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 20px;
                padding: 2.5rem;
                color: white;
                margin-bottom: 2rem;
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.2);
            }
            
            .journal-title {
                font-size: 2.5rem;
                font-weight: 800;
                margin: 0 0 0.5rem 0;
            }
            
            .journal-subtitle {
                margin: 0;
                opacity: 0.9;
            }
            
            .entry-card {
                background: white;
                border-radius: 15px;
                padding: 1.5rem;
                margin-bottom: 1rem;
                box-shadow: 0 5px 15px rgba(0,0,0,0.05);
                border-left: 4px solid #9370DB;
                transition: all 0.3s ease;
            }
            
            .entry-card:hover {
                box-shadow: 0 15px 40px rgba(102, 126, 234, 0.15);
                transform: translateY(-3px);
            }
            
            .emotion-badge {
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 50px;
                font-weight: 600;
                font-size: 0.9rem;
                margin-right: 0.5rem;
            }
        </style>
        
        <div class="journal-header">
            <h1 class="journal-title">📔 My Journal</h1>
            <p class="journal-subtitle">Reflect, analyze, and grow</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # New Entry Section
    st.markdown("### ✨ Write a New Entry")
    text = st.text_area("What's on your mind?", height=150, placeholder="Share your thoughts, feelings, experiences...")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("💾 Save Entry", key="save-entry", use_container_width=True):
            if text.strip():
                r = create_entry(text)
                if r.status_code in [200, 201]:
                    st.success("✅ Entry saved successfully!")
                    safe_rerun()
                else:
                    st.error("Failed to save")
            else:
                st.warning("Please write something")
    
    st.markdown("---")
    
    # Entries List
    st.markdown("### 📚 Your Entries")
    r = list_entries()
    if r.status_code != 200:
        st.error("Could not load entries")
        return

    raw_entries = r.json().get("entries", []) or []
    if not raw_entries:
        st.info("No entries yet — start writing to begin your journey!")
        return

    processed = []
    for e in raw_entries:
        created_raw = e.get("created_at") or ""
        try:
            dt = pd.to_datetime(created_raw)
            if pd.isna(dt):
                dt = None
        except:
            dt = None
        processed.append({**e, "_dt": dt})

    processed.sort(key=lambda x: x["_dt"] if x["_dt"] is not None else pd.Timestamp.min, reverse=True)

    def date_key(item):
        dt = item.get("_dt")
        return dt.date() if dt is not None else None

    grouped = []
    for key, group in groupby(processed, key=date_key):
        grouped.append((key, list(group)))

    for date_key, entries_for_date in grouped:
        date_label = date_key.strftime("%d %B %Y") if date_key else "Unknown Date"
        
        with st.expander(f"{date_label} ({len(entries_for_date)} entries)", expanded=True):
            for e in entries_for_date:
                e_id = e.get("id") or f"no-id-{hash(e.get('content',''))}"
                dt = e.get("_dt")
                time_str = dt.strftime("%I:%M %p") if dt else "Unknown"
                content = e.get("content", "")

                mood = e.get("mood_analysis") or {}
                emotion = mood.get("emotion", "Unknown")
                sentiment = mood.get("sentiment", "Unknown")
                score = mood.get("score", 0.0)

                st.markdown(
                    f"""
                    <div class="entry-card">
                        <div style='display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;'>
                            <div>
                                <h3 style='color: #667eea; margin: 0; font-size: 1.3rem;'>{emotion}</h3>
                                <p style='color: #999; margin: 0.2rem 0 0 0; font-size: 0.85rem;'>{time_str}</p>
                            </div>
                            <div style='text-align: right;'>
                                <p style='color: #666; margin: 0; font-size: 0.85rem;'><strong>Confidence:</strong> {score:.0%}</p>
                            </div>
                        </div>
                        
                        <p style='background: #f5f5f5; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; color: #333; line-height: 1.6;'>{content}</p>
                        
                        <div>
                            <span class="emotion-badge">{emotion}</span>
                            <span class="emotion-badge" style='background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);'>{sentiment}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️ Edit", key=f"edit-{e_id}", use_container_width=True):
                        st.session_state[f"edit_mode_{e_id}"] = True
                        safe_rerun()
                with col2:
                    if st.button("🗑️ Delete", key=f"del-{e_id}", use_container_width=True):
                        dr = delete_entry(e_id)
                        if dr.status_code in (200, 204):
                            st.success("Deleted!")
                            safe_rerun()
                        else:
                            st.error("Delete failed")

# --- DASHBOARD PAGE ---
def render_dashboard_page():
    if not st.session_state.get("token"):
        st.warning("Please log in to view the dashboard.")
        return

    st.markdown(
        """
        <div class="journal-header">
            <h1 class="journal-title">📊 Your Mood Insights</h1>
            <p class="journal-subtitle">Track your emotional journey</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    r = list_entries()
    if r.status_code != 200:
        st.error("Could not load dashboard")
        return

    entries = r.json().get("entries", [])
    if not entries:
        st.info("No mood data yet. Write some entries first!")
        return
    
    rows = []
    for e in entries:
        mood = e.get("mood_analysis")
        if mood:
            rows.append({
                "date": pd.to_datetime(e["created_at"]),
                "emotion": mood.get("emotion", "Unknown").capitalize(),
                "sentiment": mood.get("sentiment", "Unknown"),
                "score": mood.get("score", 0.0),
            })
    
    df = pd.DataFrame(rows)
    if df.empty:
        st.info("No mood analysis data yet.")
        return
    
    latest = df.sort_values("date", ascending=False).iloc[0]
    
    # Today's Mood Card
    st.markdown(
        f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 20px;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.2);
            text-align: center;
        '>
            <p style='margin: 0 0 0.5rem 0; opacity: 0.9;'>TODAY'S MOOD</p>
            <h2 style='margin: 0; font-size: 3rem;'>{latest['emotion']}</h2>
            <p style='margin: 1rem 0 0 0;'>
                <strong>{latest['sentiment']}</strong> • Confidence <strong>{latest['score']:.0%}</strong>
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Stats Grid
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📝 Total Entries", len(df))
    
    with col2:
        most_common = df['emotion'].value_counts().idxmax()
        st.metric("😊 Most Common Mood", most_common)
    
    with col3:
        avg_confidence = df['score'].mean()
        st.metric("⭐ Avg Confidence", f"{avg_confidence:.0%}")
    
    st.markdown("---")
    
    # Charts
    st.markdown("### 📈 Weekly Mood Trend")
    one_week_ago = datetime.now() - timedelta(days=7)
    df_week = df[df["date"] >= one_week_ago]

    if not df_week.empty:
        df_week["day"] = df_week["date"].dt.day_name()
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        weekly_stats = df_week.groupby(["day", "emotion"]).size().reset_index(name="count")
        
        chart = alt.Chart(weekly_stats).mark_bar().encode(
            x=alt.X("day:N", sort=day_order),
            y="count:Q",
            color="emotion:N"
        ).properties(height=300)
        
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No data for this week")
    
    st.markdown("### 🎯 Overall Emotion Distribution")
    emotion_counts = df['emotion'].value_counts().reset_index()
    emotion_counts.columns = ['emotion', 'count']
    
    pie_chart = alt.Chart(emotion_counts).mark_arc().encode(
        theta="count:Q",
        color="emotion:N"
    ).properties(height=400)
    
    st.altair_chart(pie_chart, use_container_width=True)

# --- MAIN ---
def main():
    st.set_page_config(
        page_title="MindFlow - AI Journal",
        layout="wide",
        page_icon="✨",
        initial_sidebar_state="expanded"
    )

    # --- Global Styling ---
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        html, body, .stApp {
            background: linear-gradient(135deg, #ffffff 0%, #f5f7ff 100%) !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
            color: #1a1a1a !important;
        }
        
        .main .block-container {
            max-width: 1200px;
            padding: 2rem 2rem !important;
        }
        
        /* Input styling */
        input, textarea, .stTextInput input, .stTextArea textarea {
            background: white !important;
            border: 1px solid #e0e0e0 !important;
            border-radius: 10px !important;
            padding: 0.75rem 1rem !important;
            font-family: 'Inter', sans-serif !important;
            transition: all 0.3s ease !important;
        }
        
        input:focus, textarea:focus {
            border-color: #667eea !important;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
            outline: none !important;
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 0.75rem 1.5rem !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .stButton > button:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3) !important;
        }
        
        /* Checkbox */
        .stCheckbox input { accent-color: #667eea !important; }
        
        /* Messages */
        .stSuccess, .stError, .stWarning, .stInfo {
            border-radius: 12px !important;
            padding: 1rem !important;
            margin: 1rem 0 !important;
        }
        
        .stSuccess {
            background: linear-gradient(135deg, rgba(76, 175, 80, 0.1), rgba(56, 142, 60, 0.1)) !important;
            border-left: 4px solid #4CAF50 !important;
        }
        
        hr {
            border: none !important;
            height: 2px !important;
            background: linear-gradient(90deg, transparent, #667eea, transparent) !important;
            margin: 2rem 0 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    initialize_session_state()
    render_sidebar()

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
        safe_rerun()

if __name__ == "__main__":
    main()
