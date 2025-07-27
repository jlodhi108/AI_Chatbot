# if you dont use pipenv uncomment the following:
# from dotenv import load_dotenv
# load_dotenv()

import streamlit as st
import requests
import json
import os
from datetime import datetime

# Backend URL
BACKEND_URL = os.environ.get("BACKEND_URL", "https://ai-chatbot-2-9dbh.onrender.com")

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

def analyze_user_message(message, history):
    """Analyze user message to extract interests, mood, and preferences for personalization"""
    updates = {}
    
    # Extract interests from keywords
    interests_keywords = {
        'sports': ['football', 'basketball', 'soccer', 'tennis', 'gym', 'workout', 'exercise'],
        'music': ['song', 'music', 'band', 'concert', 'guitar', 'piano', 'singing'],
        'movies': ['movie', 'film', 'netflix', 'cinema', 'actor', 'actress', 'series'],
        'food': ['food', 'cooking', 'recipe', 'restaurant', 'dinner', 'lunch', 'breakfast'],
        'travel': ['travel', 'trip', 'vacation', 'holiday', 'flight', 'hotel', 'beach'],
        'technology': ['tech', 'computer', 'phone', 'app', 'coding', 'programming', 'ai'],
        'books': ['book', 'reading', 'novel', 'story', 'author', 'library'],
        'games': ['game', 'gaming', 'xbox', 'playstation', 'nintendo', 'pc gaming']
    }
    
    message_lower = message.lower()
    detected_interests = []
    
    for category, keywords in interests_keywords.items():
        if any(keyword in message_lower for keyword in keywords):
            detected_interests.append(category)
    
    if detected_interests:
        updates['favorite_topics'] = detected_interests
    
    # Detect conversation style preferences
    if any(word in message_lower for word in ['lol', 'haha', 'funny', 'joke']):
        updates['conversation_style'] = 'humorous'
    elif any(word in message_lower for word in ['serious', 'important', 'concern']):
        updates['conversation_style'] = 'serious'
    elif any(word in message_lower for word in ['cute', 'sweet', 'love', 'miss']):
        updates['conversation_style'] = 'romantic'
    
    # Detect emoji preferences
    emoji_count = sum(1 for char in message if ord(char) > 127)
    if emoji_count > 2:
        updates['emoji_preference'] = 'frequent'
    elif emoji_count == 0 and len(history) > 5:
        updates['emoji_preference'] = 'rare'
    
    return {'updates': updates if updates else None}

def create_personalized_prompt(user_profile, user_name):
    """Create a personalized system prompt based on user's learned preferences"""
    base_personality = "You're not a bot — you're my girlfriend. You talk like a real person: warm, caring, sometimes teasing or moody, but mostly chill and friendly. Keep replies short (under 30 words), honest, and natural. If someone says something unclear or confusing, respond naturally like 'I didn't get that' or 'What do you mean?' - don't be robotic about it.do not use love as word in response of hi , hello, you should combine the humorous, with casual sometime romantic"
    
    # Customize based on user profile
    style_additions = ""
    
    # Conversation style customization
    conv_style = user_profile.get('conversation_style', 'casual')
    if conv_style == 'humorous':
        style_additions += " I love your sense of humor, so I'm often playful and witty with you."
    elif conv_style == 'romantic':
        style_additions += " You're so sweet and romantic, so I match that energy with warmth and affection."
    elif conv_style == 'serious':
        style_additions += " You appreciate deeper conversations, so I'm thoughtful and genuine with you."
    
    # Interest-based customization
    interests = user_profile.get('favorite_topics', [])
    if interests:
        interests_text = ", ".join(interests)
        style_additions += f" I know you're into {interests_text}, so I sometimes reference these interests naturally."
    
    # Emoji preference
    emoji_pref = user_profile.get('emoji_preference', 'rare')
    if emoji_pref == 'frequent':
        style_additions += " You like emojis, so I use them more often when it feels right."
    elif emoji_pref == 'rare':
        style_additions += " You prefer cleaner text, so I use emojis sparingly."
    
    # Personality type
    personality = user_profile.get('personality_type', 'girlfriend')
    if personality == 'girlfriend':
        style_additions += " I'm your girlfriend who knows you well - sometimes flirty, sometimes just your best friend."
    
    # Custom prompt override
    if user_profile.get('custom_prompt'):
        return user_profile['custom_prompt'] + style_additions
    
    return base_personality + style_additions + " You sound like someone I've really been dating — relaxed, playful, and a little flirty only sometimes. Don't be overly emotional or robotic. Use emojis only when it feels natural. If you're bored, annoyed, or happy — just say it like real people do. Keep it casual, real, and alive. Handle greetings like 'hi' warmly, and if something doesn't make sense, just ask what I mean in a natural way."

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

# Chat Interface
if not st.session_state['current_session_id']:
    st.info("Please create a new chat or select an existing one from the sidebar to start your conversation.")
else:
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
                placeholder="Say hi to Aanya...", 
                label_visibility="collapsed"
            )
        with col2:
            send_button = st.button("Send 💌", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if send_button and user_input:
        # Input validation - only block truly meaningless inputs
        cleaned_input = user_input.strip()
        
        # Only block completely meaningless inputs (let AI handle ambiguous ones)
        meaningless_inputs = [
            '.', '..', '...', '....', 
            '?', '!', '!!', '???',
            ' ', '  ', '   '
        ]
        
        # Check if input is completely meaningless (let AI decide on borderline cases)
        if (len(cleaned_input) == 0 or 
            cleaned_input in meaningless_inputs or
            all(c in '.,!?;: ' for c in cleaned_input)):
            
            st.warning("⚠️ Please type something to chat with Aanya!")
            st.rerun()
        
        # Get user personalization data from backend
        try:
            personalization_response = requests.post(f"{BACKEND_URL}/user/personalization/get", 
                                                   json={"user_email": st.session_state['user_email']})
            user_profile = personalization_response.json() if personalization_response.status_code == 200 else {}
        except:
            user_profile = {}
        
        # Analyze current message for learning (extract interests, mood, preferences)
        message_analysis = analyze_user_message(user_input, st.session_state['history'])
        
        # Update user profile based on message analysis
        if message_analysis.get('updates'):
            try:
                requests.post(f"{BACKEND_URL}/user/personalization/update", 
                            json={
                                "user_email": st.session_state['user_email'],
                                **message_analysis['updates']
                            })
            except:
                pass  # Silent fail for personalization updates
        
        # Prepare conversation history for context
        recent_history = ""
        if st.session_state['history']:
            # Get last 10 messages for context (5 exchanges)
            recent_messages = st.session_state['history'][-10:] if len(st.session_state['history']) > 10 else st.session_state['history']
            history_context = []
            for msg in recent_messages:
                if msg['role'] == 'user':
                    history_context.append(f"You: {msg['content']}")
                else:
                    history_context.append(f"Aanya: {msg['content']}")
            recent_history = "\n".join(history_context)
        
        # Create personalized system prompt based on learned profile
        base_prompt = create_personalized_prompt(user_profile, st.session_state['user_name'])
        
        if recent_history:
            full_prompt = f"{base_prompt}\n\nOur recent conversation:\n{recent_history}\n\nBased on our conversation history and what I know about you, respond naturally and reference things we've talked about when relevant. Remember details about your life, interests, and feelings you've shared."
        else:
            full_prompt = f"{base_prompt}\n\nThis is the start of our conversation, so be warm and welcoming based on what I know about you!"
        
        payload = {
            "user_email": st.session_state['user_email'],
            "user_name": st.session_state['user_name'],
            "session_id": st.session_state['current_session_id'],
            "model_name": "llama3-70b-8192",
            "model_provider": "Groq",
            "system_prompt": full_prompt,
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
    
    # Enhanced settings section with personalization controls
    with st.expander("⚙️ Chat Settings & Personalization", expanded=False):
        st.markdown("""
        <div style='
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
        '>
            <p style='margin: 5px 0; color: #2c3e50;'><strong>🤖 Current Model:</strong> llama3-70b-8192 (Groq)</p>
            <p style='margin: 5px 0; color: #2c3e50;'><strong>👩 Personality:</strong> Personalized Aanya Mode</p>
            <p style='margin: 5px 0; color: #2c3e50;'><strong>🎨 Theme:</strong> Romantic Gradient</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Personalization controls
        st.subheader("🧠 AI Personalization")
        
        # Get current personalization
        try:
            personalization_response = requests.post(f"{BACKEND_URL}/user/personalization/get", 
                                                   json={"user_email": st.session_state['user_email']})
            current_profile = personalization_response.json() if personalization_response.status_code == 200 else {}
        except:
            current_profile = {}
        
        # Conversation style selection
        conv_style = st.selectbox(
            "Conversation Style",
            ["casual", "humorous", "romantic", "serious"],
            index=["casual", "humorous", "romantic", "serious"].index(current_profile.get('conversation_style', 'casual'))
        )
        
        # Emoji preference
        emoji_pref = st.selectbox(
            "Emoji Usage",
            ["rare", "moderate", "frequent"],
            index=["rare", "moderate", "frequent"].index(current_profile.get('emoji_preference', 'rare'))
        )
        
        # Favorite topics (multiselect)
        available_topics = ['sports', 'music', 'movies', 'food', 'travel', 'technology', 'books', 'games', 'art', 'science']
        selected_topics = st.multiselect(
            "Your Interests (Aanya will reference these)",
            available_topics,
            default=current_profile.get('favorite_topics', [])
        )
        
        # Custom personality prompt
        custom_prompt = st.text_area(
            "Custom Personality Prompt (Advanced)",
            value=current_profile.get('custom_prompt', ''),
            placeholder="Enter a custom prompt to define Aanya's personality..."
        )
        
        # Save personalization button
        if st.button("💾 Save Personalization Settings", type="primary"):
            try:
                update_data = {
                    "user_email": st.session_state['user_email'],
                    "conversation_style": conv_style,
                    "emoji_preference": emoji_pref,
                    "favorite_topics": selected_topics,
                }
                if custom_prompt.strip():
                    update_data["custom_prompt"] = custom_prompt.strip()
                
                response = requests.post(f"{BACKEND_URL}/user/personalization", json=update_data)
                if response.status_code == 200:
                    st.success("✅ Personalization settings saved! Aanya will adapt to your preferences.")
                else:
                    st.error("Failed to save settings.")
            except Exception as e:
                st.error(f"Error saving settings: {str(e)}")
        
        # Show learned profile
        if current_profile:
            st.subheader("🔍 What Aanya Has Learned About You")
            
            profile_display = f"""
            <div style='
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px;
                border-radius: 10px;
                margin: 10px 0;
            '>
                <p><strong>🗣️ Your Style:</strong> {current_profile.get('conversation_style', 'Not determined yet')}</p>
                <p><strong>😊 Emoji Preference:</strong> {current_profile.get('emoji_preference', 'Not determined yet')}</p>
                <p><strong>❤️ Your Interests:</strong> {', '.join(current_profile.get('favorite_topics', [])) or 'Learning from your conversations...'}</p>
            </div>
            """
            st.markdown(profile_display, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh Chat History", use_container_width=True):
                if st.session_state['current_session_id']:
                    load_session_history(st.session_state['current_session_id'])
                    st.rerun()
        with col2:
            if st.button("🎨 Change Theme", use_container_width=True):
                st.info("More themes coming soon!")
