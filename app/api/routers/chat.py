from typing import Any, List
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.core.config import settings
from app.api import deps
from app.db.database import get_db
from app.models.user import User
from app.models.chat import ChatSession
from app.schemas.chat import ChatSession as ChatSessionSchema, ChatSessionWithMessages
from app.services.chatbot import ChatbotService, get_chatbot_service
from app.websockets.connection_manager import manager

router = APIRouter()

# --- Helpers ---

async def get_ws_user(token: str, db: Session) -> User:
    """Dependency specifically for WebSocket Auth via querystring token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        user = db.query(User).filter(User.id == int(user_id)).first()
        return user
    except JWTError:
        return None

# --- REST Endpoints (History & Session Management) ---

@router.post("/sessions", response_model=ChatSessionSchema)
def start_chat_session(
    topic: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
    chat_svc: ChatbotService = Depends(get_chatbot_service)
) -> Any:
    """Start a new AI Chatbot session."""
    session = chat_svc.create_session(user_id=current_user.id, topic=topic)
    return session

@router.get("/sessions", response_model=List[ChatSessionSchema])
def get_chat_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 20
) -> Any:
    """Get history of all AI chat sessions for the active user."""
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.started_at.desc()).offset(skip).limit(limit).all()
    return sessions

@router.get("/sessions/{session_id}", response_model=ChatSessionWithMessages)
def get_chat_session_details(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
    chat_svc: ChatbotService = Depends(get_chatbot_service)
) -> Any:
    """Get full message history for a specific session."""
    session = chat_svc.get_session(session_id=session_id, user_id=current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

# --- WebSocket Endpoints (Real-Time Communication) ---

@router.websocket("/ws/chatbot/{session_id}")
async def websocket_chatbot_endpoint(
    websocket: WebSocket,
    session_id: int,
    token: str,
    db: Session = Depends(get_db),
    chat_svc: ChatbotService = Depends(get_chatbot_service)
):
    """
    WebSocket route for live streaming chat with the Mental Health AI.
    Requires passing `?token=<access_token>` in the connection URL.
    """
    user = await get_ws_user(token, db)
    if not user:
        await websocket.close(code=1008) # Policy Violation
        return

    # Verify session belongs to user
    session = chat_svc.get_session(session_id=session_id, user_id=user.id)
    if not session:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, user.id)
    
    try:
        while True:
            # 1. Receive User Message
            data = await websocket.receive_text()
            
            # 2. Persist User Message
            chat_svc.add_message(session_id=session_id, sender="user", content=data)
            
            # 3. Get AI Response (Simulated LLM pipeline with guardrails)
            ai_response = await chat_svc.get_ai_response(session_id=session_id, user_message=data)
            
            # 4. Persist & Send AI Response
            chat_svc.add_message(session_id=session_id, sender="ai", content=ai_response)
            await manager.send_personal_message({"sender": "ai", "content": ai_response, "session_id": session_id}, user.id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user.id)
