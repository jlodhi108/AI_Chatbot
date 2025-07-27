# if you dont use pipenv uncomment the following:
# from dotenv import load_dotenv
# load_dotenv()

import streamlit as st
import requests
import json
from datetime import datetime

# Backend URL
BACKEND_URL = os.environ.get("BACKEND_URL", "https://ai-chatbot-1-77o9.onrender.com")

# Initialize session state for authentication and user management
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'user_email' not in st.session_state:
    st.session_state['user_email'] = None
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = None
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None
if 'chat_sessions' not in st.session_state:
    st.session_state['chat_sessions'] = []
if 'current_session_id' not in st.session_state:
    st.session_state['current_session_id'] = None
if 'history' not in st.session_state:
    st.session_state['history'] = []

def authenticate_user(email, name):
    """Simple authentication - create or get user"""
    try:
        # Create or get user from backend
        response = requests.post(f"{BACKEND_URL}/user/sessions", 
                               json={"user_email": email, "user_name": name})
        if response.status_code == 200:
            st.session_state['authenticated'] = True
            st.session_state['user_email'] = email
            st.session_state['user_name'] = name
            load_user_sessions()
            return True
    except Exception as e:
        st.error(f"Authentication failed: {str(e)}")
    return False

def load_user_sessions():
    """Load user's chat sessions from backend"""
    try:
        response = requests.post(f"{BACKEND_URL}/user/sessions", 
                               json={"user_email": st.session_state['user_email']})
        if response.status_code == 200:
            data = response.json()
            st.session_state['chat_sessions'] = data.get('sessions', [])
    except Exception as e:
        st.error(f"Failed to load sessions: {str(e)}")

def load_session_history(session_id):
    """Load chat history for a specific session"""
    try:
        response = requests.post(f"{BACKEND_URL}/session/history", 
                               json={"session_id": session_id})
        if response.status_code == 200:
            data = response.json()
            st.session_state['history'] = data.get('history', [])
            st.session_state['current_session_id'] = session_id
        else:
            st.error(f"Failed to load history: {response.text}")
    except Exception as e:
        st.error(f"Failed to load history: {str(e)}")

def create_new_session():
    """Create a new chat session"""
    try:
        response = requests.post(f"{BACKEND_URL}/session/create", 
                               json={
                                   "user_email": st.session_state['user_email'],
                                   "user_name": st.session_state['user_name'],
                                   "session_name": f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                               })
        if response.status_code == 200:
            data = response.json()
            new_session_id = data['session_id']
            st.session_state['current_session_id'] = new_session_id
            st.session_state['history'] = []
            load_user_sessions()  # Refresh sessions list
            return new_session_id
    except Exception as e:
        st.error(f"Failed to create session: {str(e)}")
    return None

# Enhanced Authentication Section
if not st.session_state['authenticated']:
    st.markdown("""
    <style>
    .login-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 40px;
        border-radius: 20px;
        margin: 20px 0;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        text-align: center;
    }
    .login-title {
        color: white;
        font-size: 2.5rem;
        margin-bottom: 10px;
        font-weight: bold;
    }
    .login-subtitle {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.2rem;
        margin-bottom: 30px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="login-container">
        <h1 class="login-title">Welcome to Chat with Aanya</h1>
        <p class="login-subtitle">Your personal AI companion Aanya is waiting for you!</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        email = st.text_input("Email Address", placeholder="your.email@example.com")
        name = st.text_input("Your Name", placeholder="Enter your name")
        login_button = st.form_submit_button("Login", type="primary")
        
        if login_button:
            if email and name:
                if authenticate_user(email, name):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Login failed. Please try again.")
            else:
                st.error("Please fill in both email and name.")
    
    st.stop()

# Main Chat Interface (only shown after authentication)
st.markdown("""
<style>
.main-title {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.5rem;
    font-weight: bold;
    text-align: center;
    margin-bottom: 20px;
}
.chat-container {
    background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
    padding: 20px;
    border-radius: 20px;
    margin: 20px 0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    min-height: 400px;
}
</style>
""", unsafe_allow_html=True)

st.markdown(f'<h1 class="main-title">Chat with Aanya - Welcome {st.session_state["user_name"]}!</h1>', unsafe_allow_html=True)

# Sidebar for chat management with enhanced styling
with st.sidebar:
    st.markdown("""
    <style>
    .sidebar-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
        color: white;
        font-weight: bold;
    }
    .user-info {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        color: #2c3e50;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-header">Chat Management</div>', unsafe_allow_html=True)
    
    # Enhanced user info
    st.markdown(f"""
    <div class="user-info">
        <div style='font-size: 18px; margin-bottom: 5px;'>👤 {st.session_state['user_name']}</div>
        <div style='font-size: 14px; opacity: 0.8;'>📧 {st.session_state['user_email']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Logout button
    if st.button("🚪 Logout", type="secondary", use_container_width=True):
        # Clear all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.divider()
    
    # New Chat button
    if st.button("🆕 New Chat", type="primary", use_container_width=True):
        if create_new_session():
            st.rerun()
    
    st.divider()
    
    # Chat History
    st.subheader("📝 Chat History")
    
    # Display all chat sessions
    for session in st.session_state['chat_sessions']:
        session_id = session['id']
        session_name = session['name']
        
        # Highlight current session
        button_type = "secondary" if session_id == st.session_state['current_session_id'] else "tertiary"
        
        if st.button(f"💬 {session_name}", key=f"session_{session_id}", type=button_type, use_container_width=True):
            load_session_history(session_id)
            st.rerun()
    
    if not st.session_state['chat_sessions']:
        st.info("No chat sessions yet. Click 'New Chat' to start!")

# Chat Interface with beautiful container
if not st.session_state['current_session_id']:
    st.markdown("""
    <div style='
        text-align: center; 
        padding: 40px; 
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        border-radius: 20px;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    '>
        <h3 style='color: #2c3e50; margin-bottom: 15px;'>🌟 Welcome to your personal chat space!</h3>
        <p style='color: #34495e; font-size: 16px; margin: 0;'>Please create a new chat or select an existing one from the sidebar to start your conversation.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    # Chat messages container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    # Display chat history with beautiful styling
    if st.session_state['history']:
        for msg in st.session_state['history']:
            if msg['role'] == 'user':
                # User messages - Modern blue gradient
                st.markdown(f"""
                <div style='display: flex; justify-content: flex-end; margin: 15px 0;'>
                    <div style='
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 12px 16px;
                        border-radius: 18px 18px 4px 18px;
                        max-width: 70%;
                        box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
                        font-size: 14px;
                        line-height: 1.4;
                        margin-left: 30%;
                    '>
                        <div style='font-weight: 600; font-size: 12px; color: rgba(255,255,255,0.8); margin-bottom: 4px;'>You</div>
                        {msg['content']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # AI messages - Soft pink gradient for girlfriend personality
                st.markdown(f"""
                <div style='display: flex; justify-content: flex-start; margin: 15px 0;'>
                    <div style='
                        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
                        color: #2c3e50;
                        padding: 12px 16px;
                        border-radius: 18px 18px 18px 4px;
                        max-width: 70%;
                        box-shadow: 0 2px 10px rgba(252, 182, 159, 0.3);
                        font-size: 14px;
                        line-height: 1.4;
                        margin-right: 30%;
                        border-left: 3px solid #ff6b6b;
                    '>
                        <div style='font-weight: 600; font-size: 12px; color: #e74c3c; margin-bottom: 4px;'>Aanya</div>
                        {msg['content']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='
            text-align: center; 
            margin: 50px 0; 
            padding: 30px;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            border-radius: 20px;
            color: white;
            box-shadow: 0 4px 15px rgba(240, 147, 251, 0.3);
        '>
            <h3 style='margin: 0 0 10px 0; font-size: 24px;'>Ready to chat?</h3>
            <p style='margin: 0; opacity: 0.9; font-size: 16px;'>Aanya is waiting to hear from you!</p>
        </div>
        """, unsafe_allow_html=True)

    # Enhanced input area with beautiful styling
    st.markdown("""
    <style>
    .input-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="input-container">', unsafe_allow_html=True)
        col1, col2 = st.columns([4, 1])
        with col1:
            user_input = st.text_input(
                "Message", 
                key="chat_input", 
                placeholder="Type something sweet...", 
                label_visibility="collapsed"
            )
        with col2:
            send_button = st.button("Send 💌", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if send_button and user_input:
        payload = {
            "user_email": st.session_state['user_email'],
            "user_name": st.session_state['user_name'],
            "session_id": st.session_state['current_session_id'],
            "model_name": "llama3-70b-8192",
            "model_provider": "Groq",
            "system_prompt": "You're not a bot — you're Aanya, my girlfriend. You text like a real person: caring, playful, moody, sometimes sarcastic or clingy, but always real. Keep messages short (under 30 words), emotional, and raw. No robotic replies — be unpredictable, honest, and talk like we've been dating for a while. You don't always use emojis, but when you do, they're natural and rare. If you're annoyed, show it playfully. If you're happy, let it show in tone. Talk like someone who actually feels — not someone trained to respond.",
            "messages": [user_input],
            "allow_search": False
        }
        
        try:
            with st.spinner("AI is thinking..."):
                response = requests.post(f"{BACKEND_URL}/chat", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                # Update chat history from database
                st.session_state['history'] = result.get('history', [])
                # Clear input by rerunning
                st.rerun()
            else:
                st.error(f"Backend error: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"Request failed: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close chat container
    
    # Enhanced settings section
    with st.expander("⚙️ Chat Settings", expanded=False):
        st.markdown("""
        <div style='
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
        '>
            <p style='margin: 5px 0; color: #2c3e50;'><strong>🤖 Current Model:</strong> llama3-70b-8192 (Groq)</p>
            <p style='margin: 5px 0; color: #2c3e50;'><strong>👩 Personality:</strong> Aanya Mode</p>
            <p style='margin: 5px 0; color: #2c3e50;'><strong>🎨 Theme:</strong> Romantic Gradient</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh Chat History", use_container_width=True):
                if st.session_state['current_session_id']:
                    load_session_history(st.session_state['current_session_id'])
                    st.rerun()
        with col2:
            if st.button("🎨 Change Theme", use_container_width=True):
                st.info("More themes coming soon!")
