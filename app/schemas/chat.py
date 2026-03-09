from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

# --- Chat Messages (AI) ---

class ChatMessageBase(BaseModel):
    sender: str
    content: str

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessage(ChatMessageBase):
    id: int
    session_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Chat Sessions (AI) ---

class ChatSessionBase(BaseModel):
    topic_summary: Optional[str] = None
    is_active: bool = True

class ChatSessionCreate(ChatSessionBase):
    pass

class ChatSessionMergeData(ChatSessionBase):
    is_active: Optional[bool] = None

class ChatSession(ChatSessionBase):
    id: int
    user_id: int
    started_at: datetime
    
    class Config:
        from_attributes = True

class ChatSessionWithMessages(ChatSession):
    messages: List[ChatMessage] = []

# --- Peer Messages ---

class PeerMessageBase(BaseModel):
    content: str

class PeerMessageCreate(PeerMessageBase):
    receiver_id: int # Who we are sending it to, determines conversation

class PeerMessage(PeerMessageBase):
    id: int
    conversation_id: int
    sender_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Peer Conversations ---

class PeerConversationBase(BaseModel):
    pass

class PeerConversation(PeerConversationBase):
    id: int
    user1_id: int
    user2_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
        
class PeerConversationWithMessages(PeerConversation):
    messages: List[PeerMessage] = []

# --- WebSocket Envelopes ---
# Used to deserialize JSON coming over WS

class WSPayload(BaseModel):
    action: str  # e.g., "send_message", "typing", "read_receipt"
    data: dict
