# Enhanced frontend with Google OAuth and personalized chat
import streamlit as st
import requests
import json
from datetime import datetime

# Configure Streamlit page
st.set_page_config(
    page_title="Personalized AI Chat",
    page_icon="💬",
    layout="wide"
)

# Mock Google OAuth (replace with actual implementation)
def mock_google_auth():
    """Mock Google authentication - replace with actual Google OAuth"""
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    
    if not st.session_state['authenticated']:
        st.title("🔐 Login Required")
        st.write("Sign in with your Google account to access personalized chat")
        
        # Mock login form
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="your.email@gmail.com")
            name = st.text_input("Display Name", placeholder="Your Name")
            
            if st.form_submit_button("Sign In with Google", type="primary"):
                if email and name:
                    st.session_state['authenticated'] = True
                    st.session_state['user_email'] = email
                    st.session_state['user_name'] = name
                    st.session_state['profile_picture'] = f"https://ui-avatars.com/api/?name={name}&background=random"
                    st.rerun()
                else:
                    st.error("Please enter both email and name")
        
        st.info("💡 **Real Implementation**: Replace this with Google OAuth using `streamlit-oauth` or similar library")
        return False
    
    return True

def load_user_sessions():
    """Load user's chat sessions from backend"""
    try:
        response = requests.post("http://127.0.0.1:9999/user/sessions", json={
            "user_email": st.session_state['user_email'],
            "user_name": st.session_state['user_name']
        })
        if response.status_code == 200:
            return response.json().get('sessions', [])
    except:
        pass
    return []

def create_new_session(session_name="New Chat"):
    """Create a new chat session"""
    try:
        response = requests.post("http://127.0.0.1:9999/session/create", json={
            "user_email": st.session_state['user_email'],
            "user_name": st.session_state['user_name'],
            "session_name": session_name
        })
        if response.status_code == 200:
            return response.json().get('session_id')
    except:
        pass
    return None

def load_session_history(session_id):
    """Load chat history for a specific session"""
    try:
        response = requests.post("http://127.0.0.1:9999/session/history", json={
            "session_id": session_id
        })
        if response.status_code == 200:
            return response.json().get('history', [])
    except:
        pass
    return []

def main_chat_interface():
    """Main chat interface after authentication"""
    
    # Initialize session state
    if 'current_session_id' not in st.session_state:
        st.session_state['current_session_id'] = None
    if 'history' not in st.session_state:
        st.session_state['history'] = []
    if 'sessions' not in st.session_state:
        st.session_state['sessions'] = load_user_sessions()
    
    # Sidebar for user profile and chat management
    with st.sidebar:
        # User Profile
        st.header("👤 Profile")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(st.session_state.get('profile_picture', ''), width=60)
        with col2:
            st.write(f"**{st.session_state['user_name']}**")
            st.write(f"{st.session_state['user_email']}")
        
        if st.button("🚪 Logout", type="secondary"):
            for key in ['authenticated', 'user_email', 'user_name', 'profile_picture']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        st.divider()
        
        # Chat Management
        st.header("💬 Chat Management")
        
        # New Chat button
        if st.button("🆕 New Chat", type="primary", use_container_width=True):
            session_id = create_new_session()
            if session_id:
                st.session_state['current_session_id'] = session_id
                st.session_state['history'] = []
                st.session_state['sessions'] = load_user_sessions()
                st.rerun()
        
        st.divider()
        
        # Chat History
        st.subheader("📝 Chat History")
        
        # Refresh sessions
        if st.button("🔄 Refresh", type="tertiary"):
            st.session_state['sessions'] = load_user_sessions()
            st.rerun()
        
        # Display sessions
        for session in st.session_state['sessions']:
            session_id = session['id']
            session_name = session['name']
            created_at = session['created_at']
            
            # Create preview
            preview = session_name[:25] + "..." if len(session_name) > 25 else session_name
            
            # Highlight current session
            button_type = "secondary" if session_id == st.session_state['current_session_id'] else "tertiary"
            
            if st.button(f"💬 {preview}", key=f"session_{session_id}", type=button_type, use_container_width=True):
                st.session_state['current_session_id'] = session_id
                st.session_state['history'] = load_session_history(session_id)
                st.rerun()
            
            # Show date
            st.caption(f"📅 {created_at[:16]}")
        
        st.divider()
        
        # Personalization Settings
        with st.expander("⚙️ Personalization"):
            personality = st.selectbox("Personality Type", 
                ["girlfriend", "friend", "mentor", "professional"],
                key="personality_setting")
            
            style = st.selectbox("Conversation Style",
                ["casual", "formal", "playful", "serious"],
                key="style_setting")
            
            emoji_pref = st.selectbox("Emoji Usage",
                ["rare", "moderate", "frequent", "none"],
                key="emoji_setting")
            
            custom_prompt = st.text_area("Custom Instructions",
                placeholder="Additional instructions for the AI...",
                key="custom_prompt_setting")
            
            if st.button("💾 Save Settings"):
                # Save personalization settings
                try:
                    requests.post("http://127.0.0.1:9999/user/personalization", json={
                        "user_email": st.session_state['user_email'],
                        "user_name": st.session_state['user_name'],
                        "personality_type": personality,
                        "conversation_style": style,
                        "emoji_preference": emoji_pref,
                        "custom_prompt": custom_prompt
                    })
                    st.success("Settings saved!")
                except:
                    st.error("Failed to save settings")
    
    # Main chat area
    st.title("💬 Personalized AI Chat")
    
    if not st.session_state['current_session_id']:
        st.info("👈 Create a new chat or select an existing one from the sidebar to start chatting!")
        return
    
    # Display current session info
    current_session = next((s for s in st.session_state['sessions'] if s['id'] == st.session_state['current_session_id']), None)
    if current_session:
        st.caption(f"💬 **{current_session['name']}** - Created: {current_session['created_at'][:16]}")
    
    # Display chat history
    if st.session_state['history']:
        for msg in st.session_state['history']:
            role = "You" if msg['role'] == 'user' else "AI"
            timestamp = msg.get('timestamp', '')
            
            if msg['role'] == 'user':
                st.markdown(f"""
                <div style='text-align: right; margin: 10px 0;'>
                    <div style='display: inline-block; padding: 10px 15px; background-color: #007ACC; color: white; border-radius: 15px 15px 5px 15px; max-width: 70%;'>
                        <strong>{role}:</strong> {msg['content']}
                    </div>
                    <div style='font-size: 0.8em; color: #666; margin-top: 2px;'>{timestamp[:16] if timestamp else ''}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='text-align: left; margin: 10px 0;'>
                    <div style='display: inline-block; padding: 10px 15px; background-color: #f0f0f0; color: black; border-radius: 15px 15px 15px 5px; max-width: 70%;'>
                        <strong>{role}:</strong> {msg['content']}
                    </div>
                    <div style='font-size: 0.8em; color: #666; margin-top: 2px;'>{timestamp[:16] if timestamp else ''}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Input area
    with st.container():
        col1, col2 = st.columns([4, 1])
        with col1:
            user_input = st.text_input("", key="chat_input", placeholder="Type your message here...", label_visibility="collapsed")
        with col2:
            send_button = st.button("Send", type="primary")

    if send_button and user_input:
        # Get personalized system prompt
        base_prompt = "You're not a bot — you're my girlfriend. You text like a real person: caring, playful, moody, sometimes sarcastic or clingy, but always real. Keep messages short (under 30 words), emotional, and raw. No robotic replies — be unpredictable, honest, and talk like we've been dating for a while. You don't always use emojis, but when you do, they're natural and rare. If you're annoyed, show it playfully. If you're happy, let it show in tone. Talk like someone who actually feels — not someone trained to respond."
        
        payload = {
            "user_email": st.session_state['user_email'],
            "user_name": st.session_state['user_name'],
            "session_id": st.session_state['current_session_id'],
            "model_name": "llama3-70b-8192",
            "model_provider": "Groq",
            "system_prompt": base_prompt,
            "messages": [user_input],
            "allow_search": False
        }
        
        try:
            with st.spinner("AI is thinking..."):
                response = requests.post("http://127.0.0.1:9999/chat", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                # Update history
                st.session_state['history'] = result.get('history', [])
                # Update sessions if needed
                st.session_state['sessions'] = load_user_sessions()
                # Clear input by rerunning
                st.rerun()
            else:
                st.error(f"Backend error: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"Request failed: {str(e)}")

# Main application flow
if __name__ == "__main__":
    if mock_google_auth():
        main_chat_interface()
