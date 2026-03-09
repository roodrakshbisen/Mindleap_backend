from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class ChatSession(Base):
    """Conversations between a user and the AI."""
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    topic_summary = Column(String(255), nullable=True)
    
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")

class ChatMessage(Base):
    """Individual messages in an AI chat session."""
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"))
    sender = Column(String(50), nullable=False) # "user" or "ai"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("ChatSession", back_populates="messages")
    __table_args__ = (Index('idx_chat_session_time', 'session_id', 'created_at'),)

class PeerConversation(Base):
    """Direct peer-to-peer or student-counsellor messaging instances."""
    __tablename__ = "peer_conversations"
    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    user2_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    messages = relationship("PeerMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="PeerMessage.created_at")

class PeerMessage(Base):
    """Individual messages in a peer-to-peer conversation."""
    __tablename__ = "peer_messages"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("peer_conversations.id", ondelete="CASCADE"))
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    conversation = relationship("PeerConversation", back_populates="messages")
    __table_args__ = (Index('idx_peer_conv_time', 'conversation_id', 'created_at'),)
