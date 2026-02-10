from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# ==================== Chat Schemas ====================

class ChatMessageInput(BaseModel):
    """Schema for incoming chat message"""
    user_message: str
    conversation_history: Optional[List[dict]] = []
    user_id: str = "anonymous"

class ChatMessageResponse(BaseModel):
    """Schema for chat response"""
    response: str
    confidence_score: float
    sources: List[str]
    requires_attention: bool
    conversation_id: Optional[str] = None

# ==================== Admin Schemas ====================

class DocumentUploadResponse(BaseModel):
    """Schema for document upload response"""
    status: str
    file: str
    chunks_created: int
    document_type: str
    timestamp: datetime

class UnansweredQueryResponse(BaseModel):
    """Schema for unanswered query"""
    id: str
    user_query: str
    confidence_score: float
    admin_response: Optional[str]
    status: str
    created_at: datetime

class AdminResponseInput(BaseModel):
    """Schema for admin responding to query"""
    query_id: str
    response: str

# ==================== Stats Schemas ====================

class StatsResponse(BaseModel):
    """Schema for dashboard statistics"""
    total_queries: int
    unanswered_count: int
    avg_confidence: float
    total_documents: int
    timestamp: datetime
