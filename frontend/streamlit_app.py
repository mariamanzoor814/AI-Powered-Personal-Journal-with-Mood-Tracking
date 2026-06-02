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
def render_navbar():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.markdown(
            """
            <div style='
                font-size: 1.5rem;
                font-weight: 800;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin: 0;
            '>
                ✨ MindFlow
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col3:
        if st.session_state.get("token"):
            nav_col1, nav_col2, nav_col3 = st.columns(3)
            with nav_col1:
                if st.button("📔 Journal", key="nav-journal", use_container_width=True):
                    st.session_state.page = "journal"
                    safe_rerun()
            with nav_col2:
                if st.button("📊 Dashboard", key="nav-dashboard", use_container_width=True):
                    st.session_state.page = "dashboard"
                    safe_rerun()
            with nav_col3:
                if st.button("🚪 Logout", key="nav-logout", use_container_width=True):
                    clear_token()
                    st.session_state.username = None
                    st.session_state.page = "home"
                    safe_rerun()
        else:
            nav_col1, nav_col2 = st.columns(2)
            with nav_col1:
                if st.button("📝 Sign In", key="nav-login", use_container_width=True):
                    st.session_state.page = "login"
                    safe_rerun()
            with nav_col2:
                if st.button("✨ Sign Up", key="nav-register", use_container_width=True):
                    st.session_state.page = "register"
                    safe_rerun()
    
    st.markdown("---")

def render_home_page():
    st.markdown(
        """
        <style>
            @keyframes fadeInDown {
                from {
                    opacity: 0;
                    transform: translateY(-30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            @keyframes fadeInLeft {
                from {
                    opacity: 0;
                    transform: translateX(-30px);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
            
            @keyframes fadeInRight {
                from {
                    opacity: 0;
                    transform: translateX(30px);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
            
            @keyframes float {
                0%, 100% {
                    transform: translateY(0px);
                }
                50% {
                    transform: translateY(-20px);
                }
            }
            
            @keyframes pulse {
                0%, 100% {
                    opacity: 1;
                }
                50% {
                    opacity: 0.7;
                }
            }
            
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateX(-100px);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
            
            .hero-section {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
                border-radius: 20px;
                padding: 4rem 2rem;
                text-align: center;
                margin: 2rem 0;
                position: relative;
                overflow: hidden;
                box-shadow: 0 20px 60px rgba(102, 126, 234, 0.4);
                animation: fadeInDown 1s ease-out;
            }
            
            .hero-section::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: radial-gradient(circle at 20% 50%, rgba(255,255,255,0.1) 0%, transparent 50%),
                            radial-gradient(circle at 80% 80%, rgba(255,255,255,0.1) 0%, transparent 50%);
                animation: pulse 4s ease-in-out infinite;
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
                font-size: 1.3rem;
                color: rgba(255,255,255,0.95);
                margin-top: 1rem;
                position: relative;
                z-index: 1;
                animation: fadeInUp 1.2s ease-out;
                max-width: 700px;
                margin-left: auto;
                margin-right: auto;
                line-height: 1.8;
            }
            
            .cta-button {
                display: inline-block;
                background: linear-gradient(135deg, #fff 0%, #f5f5f5 100%);
                color: #667eea;
                padding: 1rem 2.5rem;
                border-radius: 50px;
                font-weight: 700;
                font-size: 1.1rem;
                border: none;
                cursor: pointer;
                margin-top: 2rem;
                box-shadow: 0 15px 35px rgba(102, 126, 234, 0.3);
                transition: all 0.3s ease;
                animation: fadeInUp 1.4s ease-out;
            }
            
            .cta-button:hover {
                transform: translateY(-5px);
                box-shadow: 0 25px 50px rgba(102, 126, 234, 0.4);
            }
            
            .feature-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 2rem;
                margin: 4rem 0;
            }
            
            .feature-card {
                background: white;
                border-radius: 15px;
                padding: 2rem;
                text-align: center;
                box-shadow: 0 10px 30px rgba(0,0,0,0.08);
                border: 1px solid rgba(102, 126, 234, 0.1);
                transition: all 0.3s ease;
                animation: fadeInUp 1s ease-out backwards;
            }
            
            .feature-card:nth-child(1) {
                animation-delay: 0.1s;
            }
            
            .feature-card:nth-child(2) {
                animation-delay: 0.2s;
            }
            
            .feature-card:nth-child(3) {
                animation-delay: 0.3s;
            }
            
            .feature-card:hover {
                transform: translateY(-15px);
                box-shadow: 0 20px 50px rgba(102, 126, 234, 0.2);
                border-color: rgba(102, 126, 234, 0.3);
            }
            
            .feature-icon {
                font-size: 3rem;
                margin-bottom: 1rem;
                animation: float 3s ease-in-out infinite;
            }
            
            .feature-card:nth-child(2) .feature-icon {
                animation-delay: -1s;
            }
            
            .feature-card:nth-child(3) .feature-icon {
                animation-delay: -2s;
            }
            
            .feature-title {
                font-size: 1.3rem;
                font-weight: 700;
                color: #333;
                margin: 0 0 0.5rem 0;
            }
            
            .feature-desc {
                color: #666;
                font-size: 0.95rem;
                line-height: 1.6;
                margin: 0;
            }
            
            .stats-section {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 2rem;
                margin: 4rem 0;
                animation: fadeInUp 1.5s ease-out;
            }
            
            .stat-card {
                text-align: center;
            }
            
            .stat-number {
                font-size: 2.5rem;
                font-weight: 900;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .stat-label {
                color: #666;
                margin-top: 0.5rem;
                font-size: 0.95rem;
            }
            
            .scroll-indicator {
                text-align: center;
                margin-top: 3rem;
                animation: fadeInUp 1.6s ease-out;
            }
            
            .scroll-dot {
                display: inline-block;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #667eea;
                margin: 0 4px;
                animation: pulse 2s ease-in-out infinite;
            }
            
            .scroll-dot:nth-child(2) {
                animation-delay: 0.2s;
            }
            
            .scroll-dot:nth-child(3) {
                animation-delay: 0.4s;
            }
        </style>
        
        <div class="hero-section">
            <h1 class="hero-title">✨ MindFlow</h1>
            <p class="hero-subtitle">
                Transform your emotions into insights with AI-powered journaling. 
                Discover patterns, track your mood, and elevate your mental well-being every day.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col_cta = st.columns([1, 2, 1])
    with col_cta[1]:
        if st.button("🚀 Start Your Journey", key="cta-btn", use_container_width=True):
            st.session_state.page = "login"
            safe_rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Features Grid
    st.markdown(
        """
        <h2 style='text-align: center; font-size: 2rem; color: #333; margin: 3rem 0 2rem 0;'>
            Why Choose MindFlow?
        </h2>
        """,
        unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns(3, gap="large")
    
    with col1:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">😊</div>
                <h3 class="feature-title">AI Emotion Detection</h3>
                <p class="feature-desc">
                    Advanced AI analyzes your entries to detect emotions, sentiment, and patterns 
                    you might not notice on your own.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <h3 class="feature-title">Beautiful Analytics</h3>
                <p class="feature-desc">
                    Visualize your mood trends with stunning charts and insights. 
                    Track daily, weekly, and monthly patterns at a glance.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">💡</div>
                <h3 class="feature-title">Smart Recommendations</h3>
                <p class="feature-desc">
                    Receive personalized, context-aware suggestions for improving 
                    your mental health and well-being.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Stats Section
    st.markdown(
        """
        <div style='text-align: center; margin: 5rem 0 2rem 0;'>
            <h2 style='font-size: 2rem; color: #333; margin: 0;'>Trusted by Thousands</h2>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    
    with stat_col1:
        st.markdown(
            """
            <div class="stat-card">
                <div class="stat-number">10K+</div>
                <div class="stat-label">Active Journalers</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with stat_col2:
        st.markdown(
            """
            <div class="stat-card">
                <div class="stat-number">1M+</div>
                <div class="stat-label">Entries Analyzed</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with stat_col3:
        st.markdown(
            """
            <div class="stat-card">
                <div class="stat-number">4.9⭐</div>
                <div class="stat-label">User Rating</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # CTA Section
    st.markdown(
        """
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            padding: 3rem;
            text-align: center;
            margin: 5rem 0 2rem 0;
            box-shadow: 0 20px 60px rgba(102, 126, 234, 0.3);
            animation: fadeInUp 1.8s ease-out;
        '>
            <h2 style='color: white; margin: 0 0 1rem 0; font-size: 2rem;'>
                Ready to Transform Your Well-being?
            </h2>
            <p style='color: rgba(255,255,255,0.95); margin: 0; font-size: 1.1rem;'>
                Join thousands of users discovering their emotional patterns with MindFlow.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col_final = st.columns([1, 2, 1])
    with col_final[1]:
        if st.button("🎯 Get Started Free", key="final-cta", use_container_width=True):
            st.session_state.page = "register"
            safe_rerun()

def render_register_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            """
            <style>
                @keyframes slideInRight {
                    from {
                        opacity: 0;
                        transform: translateX(100px);
                    }
                    to {
                        opacity: 1;
                        transform: translateX(0);
                    }
                }
                
                .auth-card {
                    background: white;
                    border-radius: 20px;
                    padding: 3rem;
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
                    color: #666;
                    margin: 0 0 2rem 0;
                    font-size: 0.95rem;
                }
            </style>
            
            <div class="auth-card">
                <h2 class="auth-title">Create Account</h2>
                <p class="auth-subtitle">Join the MindFlow community today</p>
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
                    st.success("✅ Registration successful! Check your email for verification.")
                    st.session_state.email_for_verification = email
                    st.session_state.page = "verify"
                    safe_rerun()
                else:
                    try:
                        st.error(r.json().get("detail", "Registration failed."))
                    except requests.exceptions.JSONDecodeError:
                        st.error(f"Server error: {r.text}")

def render_verify_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            """
            <div class="auth-card">
                <h2 class="auth-title">Verify Account</h2>
                <p class="auth-subtitle">Enter the code sent to your email</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        email = st.text_input("📧 Email", value=st.session_state.get("email_for_verification", ""), disabled=True)
        otp = st.text_input("🔑 Verification Code", placeholder="Enter 6-digit code")

        if st.button("Verify Account", use_container_width=True):
            r = post_verify(email, otp)
            if r.status_code == 200:
                st.success("✅ Account verified! Redirecting to login...")
                st.session_state.page = "login"
                st.balloons()
                safe_rerun()
            else:
                try:
                    st.error(r.json().get("detail", "Verification failed."))
                except requests.exceptions.JSONDecodeError:
                    st.error(f"Server error: {r.text}")

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
                    st.success("✅ Logged in successfully!")
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

    st.markdown(
        """
        <h1 style='color: #667eea; margin:0 0 0.5rem 0; font-size:2.5rem;'>📔 My Journal</h1>
        <p style='color:#666; margin:0 0 2rem 0;'>Write, reflect, and discover yourself</p>
        """,
        unsafe_allow_html=True
    )
    
    # New Entry Section
    st.markdown(
        """
        <div style='
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
            border: 2px dashed rgba(102, 126, 234, 0.3);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
        '>
            <h3 style='color:#667eea; margin:0 0 1rem 0;'>✨ Write a New Entry</h3>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    text = st.text_area("What's on your mind?", height=180, key="journal_text_area", placeholder="Share your thoughts, feelings, and experiences...")
    
    col1, col2 = st.columns([3, 1])
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
    
    st.markdown(
        """
        <h2 style='color:#667eea; margin:2rem 0 1rem 0; font-size:1.8rem;'>📚 Your Entries</h2>
        """,
        unsafe_allow_html=True
    )

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

    processed.sort(key=lambda x: x["_dt"] if x["_dt"] is not None else pd.Timestamp.min, reverse=True)

    def date_key(item):
        dt = item.get("_dt")
        if dt is None:
            return None
        return dt.date()

    grouped = []
    for key, group in groupby(processed, key=date_key):
        group_list = list(group)
        grouped.append((key, group_list))

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

                mood = e.get("mood_analysis") or {}
                sentiment = mood.get("sentiment", "Unknown")
                emotion = mood.get("emotion", "Unknown")
                score = mood.get("score", 0.0)

                st.markdown(
                    f"""
                    <div style='
                        background: white;
                        border: 1px solid rgba(102, 126, 234, 0.1);
                        border-radius: 12px;
                        padding: 1.5rem;
                        margin-bottom: 1rem;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
                    '>
                        <div style='display:flex; justify-content:space-between; align-items:start; margin-bottom:1rem;'>
                            <div>
                                <h3 style='color:#667eea; margin:0; font-size:1.5rem;'>{emotion}</h3>
                                <p style='color:#999; margin:0.3rem 0 0 0; font-size:0.9rem;'>{time_str}</p>
                            </div>
                            <div style='text-align:right;'>
                                <p style='color:#666; margin:0; font-size:0.85rem;'><strong>Confidence:</strong> {score:.0%}</p>
                            </div>
                        </div>
                        
                        <div style='
                            background: #f8f8f8;
                            border-left: 3px solid #667eea;
                            padding: 1rem;
                            border-radius: 6px;
                            margin-bottom: 1rem;
                        '>
                            <p style='color:#333; margin:0; line-height:1.6; font-size:1rem;'>{content}</p>
                        </div>
                        
                        <div style='
                            background: linear-gradient(90deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
                            padding: 0.75rem 1rem;
                            border-radius: 8px;
                            margin-bottom: 1rem;
                            display:flex; gap:1rem; flex-wrap:wrap;
                        '>
                            <span style='color:#666;'><strong>Sentiment:</strong> <span style='color:#667eea;'>{sentiment}</span></span>
                            <span style='color:#666;'><strong>Mood:</strong> <span style='color:#667eea;'>{emotion}</span></span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if st.session_state.get(f"edit_mode_{e_id}", False):
                    st.markdown("<p style='color:#667eea; font-weight:600; margin-bottom:0.5rem;'>✏️ Edit Entry</p>", unsafe_allow_html=True)
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
        <h1 style='color:#667eea; margin:0 0 0.5rem 0; font-size:2.5rem;'>📊 Mood Insights</h1>
        <p style='color:#666; margin:0 0 2rem 0;'>Visualize your emotional patterns and progress</p>
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
    
    latest = df.sort_values("date", ascending=False).iloc[0]

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

    st.markdown(
        f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 16px;
            margin: 2rem 0;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.25);
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

    color_scheme = alt.Scale(scheme="tableau10")
    
    st.markdown(
        "<h2 style='color:#667eea; margin-top:2rem;'>Weekly Mood Trend</h2>",
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

    st.markdown(
        "<h2 style='color:#667eea; margin-top:2rem;'>Monthly Mood Distribution</h2>",
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

    st.markdown(
        "<h2 style='color:#667eea; margin-top:2rem;'>Overall Emotion Distribution</h2>",
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
    st.set_page_config(
        page_title="MindFlow - AI-Powered Personal Journal",
        layout="wide",
        page_icon="✨",
        initial_sidebar_state="collapsed"
    )

    # --- Modern Premium CSS ---
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    :root {
        --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        --text-primary: #1a1a1a;
        --text-secondary: #666666;
        --border-color: #e0e0e0;
    }

    html, body, .stApp {
        background: linear-gradient(135deg, #ffffff 0%, #f5f7ff 100%) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        color: var(--text-primary) !important;
    }

    .main .block-container {
        max-width: 1200px;
        padding: 2rem 2rem !important;
    }

    /* Hide sidebar */
    section[data-testid="stSidebar"] {
        display: none !important;
    }

    /* Input Styling */
    input[type="text"], input[type="password"], input[type="email"], textarea {
        background: white !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        padding: 0.75rem 1rem !important;
        font-size: 0.95rem !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
    }

    input:focus, textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
        outline: none !important;
    }

    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3) !important;
    }

    .stButton > button:active {
        transform: translateY(-1px);
    }

    /* Checkbox */
    .stCheckbox input[type="checkbox"] {
        accent-color: #667eea !important;
    }

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

    .stError {
        background: linear-gradient(135deg, rgba(244, 67, 54, 0.1), rgba(211, 47, 47, 0.1)) !important;
        border-left: 4px solid #f44336 !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.05)) !important;
        border: 1px solid rgba(102, 126, 234, 0.1) !important;
        border-radius: 10px !important;
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
    
    # Render navbar only for authenticated users
    if st.session_state.get("token"):
        render_navbar()
    
    page = st.session_state.page
    if page == "home": render_home_page()
    elif page == "register": render_register_page()
    elif page == "verify": render_verify_page()
    elif page == "login": render_login_page()
    elif page == "journal": 
        render_navbar()
        render_journal_page()
    elif page == "dashboard": 
        render_navbar()
        render_dashboard_page()
    else:
        st.session_state.page = "home"
        safe_rerun()

if __name__ == "__main__":
    main()
