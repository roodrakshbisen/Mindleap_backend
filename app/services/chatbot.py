import asyncio
from sqlalchemy.orm import Session
from app.models.chat import ChatSession, ChatMessage
from app.schemas.chat import ChatMessageCreate

class ChatbotService:
    def __init__(self, db: Session):
        self.db = db

    def create_session(self, user_id: int, topic: str = None) -> ChatSession:
        db_session = ChatSession(user_id=user_id, topic_summary=topic)
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return db_session

    def get_session(self, session_id: int, user_id: int) -> ChatSession:
        return self.db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()

    def add_message(self, session_id: int, sender: str, content: str) -> ChatMessage:
        message = ChatMessage(session_id=session_id, sender=sender, content=content)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    async def get_ai_response(self, session_id: int, user_message: str) -> str:
        """
        Simulates calling an LLM (like OpenAI/Langchain).
        In a real scenario, this would format the conversation history,
        check for crisis triggers, and stream the LLM response.
        """
        # 1. Guardrail check (Crisis intervention)
        crisis_keywords = ["suicide", "kill myself", "end it all"]
        if any(keyword in user_message.lower() for keyword in crisis_keywords):
            return "I am noticing some things in your message that concern me. You are not alone. Please reach out to the National Crisis Hotline at 988 immediately, or let me connect you with an emergency counselor on campus right now."

        # 2. Simulate network delay / LLM inference
        await asyncio.sleep(1.5)
        
        # 3. Dummy AI logic for demo purposes
        if "stress" in user_message.lower() or "exam" in user_message.lower():
            return "I hear that you're feeling stressed. Exams can be a very overwhelming time. Have you tried taking a 5-minute breathing break today?"
        
        return f"I understand. Can you tell me a little bit more about how that makes you feel?"

from fastapi import Depends
from app.db.database import get_db

def get_chatbot_service(db: Session = Depends(get_db)) -> ChatbotService:
    return ChatbotService(db)
