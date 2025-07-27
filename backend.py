# if you dont use pipenv uncomment the following:
from dotenv import load_dotenv
load_dotenv()

#Step1: Setup Pydantic Model (Schema Validation)
from pydantic import BaseModel
from typing import List, Optional

# Import database
from database import db

class RequestState(BaseModel):
    # User identification and profile
    user_email: str
    user_name: str
    session_id: Optional[int] = None
    # Chat configuration
    model_name: str
    model_provider: str
    system_prompt: str
    messages: List[str]
    allow_search: bool


#Step2: Setup AI Agent from FrontEnd Request
from fastapi import FastAPI, Request
from ai_agent import get_response_from_ai_agent

ALLOWED_MODEL_NAMES=["llama3-70b-8192", "mixtral-8x7b-32768", "llama-3.3-70b-versatile", "gpt-4o-mini"]

app=FastAPI(title="LangGraph AI Agent")

@app.post("/chat")
async def chat_endpoint(request: Request):
    # Manually parse JSON to avoid automatic validation errors
    data = await request.json()
    # Check for missing fields
    required_fields = ["user_email", "user_name", "model_name", "model_provider", "system_prompt", "messages", "allow_search"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        return {"error": f"Missing fields in request: {missing}"}
    
    user_email = data["user_email"]
    user_name = data["user_name"]
    session_id = data.get("session_id")
    model_name = data["model_name"]
    messages = data["messages"]
    allow_search = data["allow_search"]
    system_prompt = data["system_prompt"]
    model_provider = data["model_provider"]
    
    # Validate model
    if model_name not in ALLOWED_MODEL_NAMES:
        return {"error": "Invalid model name. Kindly select a valid AI model"}
    
    # Get or create user
    user_id = db.create_or_get_user(user_email, user_name)
    
    # Create new session if not provided
    if not session_id:
        session_id = db.create_chat_session(user_id)
    
    # Get user's personalization
    personalization = db.get_user_personalization(user_id)
    
    # Customize system prompt based on user's preferences
    if personalization.get('custom_prompt'):
        system_prompt = personalization['custom_prompt']
    
    # Add user message to database
    for msg in messages:
        db.add_message(session_id, "user", msg)
    
    # Get recent chat history for context (last 20 messages)
    chat_history = db.get_chat_history(session_id, limit=20)
    
    # Prepare messages for AI (include history for context)
    context_messages = []
    for msg in chat_history[:-len(messages)]:  # Exclude just-added messages
        context_messages.append(msg['content'])
    context_messages.extend(messages)  # Add current messages
    
    # Invoke AI agent
    response = get_response_from_ai_agent(model_name, context_messages, allow_search, system_prompt, model_provider)
    
    # Add AI response to database
    db.add_message(session_id, "assistant", response)
    
    # Get updated chat history
    updated_history = db.get_chat_history(session_id, limit=50)
    
    # Return response and chat history
    return {
        "response": response, 
        "history": updated_history,
        "session_id": session_id,
        "user_id": user_id
    }

@app.post("/user/sessions")
async def get_user_sessions(request: Request):
    """Get all chat sessions for a user"""
    data = await request.json()
    user_email = data.get("user_email")
    if not user_email:
        return {"error": "user_email required"}
    
    user_id = db.create_or_get_user(user_email, data.get("user_name", "User"))
    sessions = db.get_user_chat_sessions(user_id)
    return {"sessions": sessions}

@app.post("/session/create")
async def create_session(request: Request):
    """Create a new chat session"""
    data = await request.json()
    user_email = data.get("user_email")
    session_name = data.get("session_name", "New Chat")
    
    if not user_email:
        return {"error": "user_email required"}
    
    user_id = db.create_or_get_user(user_email, data.get("user_name", "User"))
    session_id = db.create_chat_session(user_id, session_name)
    return {"session_id": session_id}

@app.post("/session/history")
async def get_session_history(request: Request):
    """Get chat history for a specific session"""
    data = await request.json()
    session_id = data.get("session_id")
    if not session_id:
        return {"error": "session_id required"}
    
    history = db.get_chat_history(session_id, limit=100)
    return {"history": history}

@app.post("/user/personalization")
async def update_personalization(request: Request):
    """Update user's personalization settings"""
    data = await request.json()
    user_email = data.get("user_email")
    if not user_email:
        return {"error": "user_email required"}
    
    user_id = db.create_or_get_user(user_email, data.get("user_name", "User"))
    
    # Extract personalization fields
    updates = {}
    for key in ['personality_type', 'custom_prompt', 'conversation_style', 'emoji_preference', 'favorite_topics']:
        if key in data:
            updates[key] = data[key]
    
    if updates:
        db.update_user_personalization(user_id, **updates)
    
    return {"success": True}

@app.post("/user/personalization/get")
async def get_personalization(request: Request):
    """Get user's personalization settings"""
    data = await request.json()
    user_email = data.get("user_email")
    if not user_email:
        return {"error": "user_email required"}
    
    user_id = db.create_or_get_user(user_email, data.get("user_name", "User"))
    personalization = db.get_user_personalization(user_id)
    return personalization

@app.post("/user/personalization/update")
async def update_personalization_incremental(request: Request):
    """Incrementally update user's personalization based on conversation analysis"""
    data = await request.json()
    user_email = data.get("user_email")
    if not user_email:
        return {"error": "user_email required"}
    
    user_id = db.create_or_get_user(user_email, data.get("user_name", "User"))
    
    # Get current personalization
    current = db.get_user_personalization(user_id)
    
    # Merge favorite topics intelligently
    if 'favorite_topics' in data:
        existing_topics = set(current.get('favorite_topics', []))
        new_topics = set(data['favorite_topics'])
        merged_topics = list(existing_topics.union(new_topics))
        data['favorite_topics'] = merged_topics[:10]  # Limit to 10 topics
    
    # Extract personalization fields for update
    updates = {}
    for key in ['personality_type', 'custom_prompt', 'conversation_style', 'emoji_preference', 'favorite_topics']:
        if key in data:
            updates[key] = data[key]
    
    if updates:
        db.update_user_personalization(user_id, **updates)
    
    return {"success": True, "updated": updates}

@app.post("/user/stats")
async def get_user_stats(request: Request):
    """Get user statistics"""
    data = await request.json()
    user_email = data.get("user_email")
    if not user_email:
        return {"error": "user_email required"}
    
    user_id = db.create_or_get_user(user_email, data.get("user_name", "User"))
    stats = db.get_user_stats(user_id)
    return stats

#Step3: Run app & Explore Swagger UI Docs
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9999)