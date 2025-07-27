# Test the personalized chat system
import requests
import json

# Test backend endpoints
def test_backend():
    base_url = "http://127.0.0.1:9999"
    
    print("🧪 Testing Enhanced Backend...")
    
    # Test user session creation
    print("\n1. Testing user session creation...")
    response = requests.post(f"{base_url}/session/create", json={
        "user_email": "test@gmail.com",
        "user_name": "Test User",
        "session_name": "My First Chat"
    })
    
    if response.status_code == 200:
        session_data = response.json()
        session_id = session_data['session_id']
        print(f"✅ Session created: {session_id}")
        
        # Test chat functionality
        print("\n2. Testing chat with database storage...")
        chat_response = requests.post(f"{base_url}/chat", json={
            "user_email": "test@gmail.com",
            "user_name": "Test User",
            "session_id": session_id,
            "model_name": "llama3-70b-8192",
            "model_provider": "Groq", 
            "system_prompt": "You're a friendly AI assistant.",
            "messages": ["Hello! How are you?"],
            "allow_search": False
        })
        
        if chat_response.status_code == 200:
            chat_data = chat_response.json()
            print(f"✅ Chat response: {chat_data['response'][:50]}...")
            print(f"✅ History length: {len(chat_data['history'])}")
        else:
            print(f"❌ Chat failed: {chat_response.status_code}")
    else:
        print(f"❌ Session creation failed: {response.status_code}")
    
    # Test session listing
    print("\n3. Testing session listing...")
    sessions_response = requests.post(f"{base_url}/user/sessions", json={
        "user_email": "test@gmail.com",
        "user_name": "Test User"
    })
    
    if sessions_response.status_code == 200:
        sessions = sessions_response.json()['sessions']
        print(f"✅ Found {len(sessions)} sessions for user")
        for session in sessions:
            print(f"   - {session['name']} (ID: {session['id']})")
    else:
        print(f"❌ Session listing failed: {sessions_response.status_code}")

if __name__ == "__main__":
    try:
        test_backend()
        print("\n🎉 All tests completed!")
        print("\n📋 Next steps:")
        print("1. Run: python backend.py")
        print("2. Run: streamlit run frontend_enhanced.py")
        print("3. Login with any email/name")
        print("4. Start chatting with personalized AI!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("Make sure backend is running: python backend.py")
