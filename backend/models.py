from sqlalchemy import Column, String, Text, DateTime, Float, Integer, JSON
from datetime import datetime
from .database import Base
import uuid
from sqlalchemy.dialects.postgresql import ARRAY

class ChatMessage(Base):
    """Store investor questions and chatbot responses"""
    __tablename__ = "chat_messages"
    
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=False)  # Investor/user identifier
    message = Column(Text, nullable=False)  # User's question
    response = Column(Text, nullable=False)  # Chatbot's answer
    source_documents = Column(Text)  # JSON: ["faq.pdf", "investment_guide.pdf"]
    confidence_score = Column(Float)  # 0.0 to 1.0
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UnansweredQuery(Base):
    """Track queries with low confidence for admin review"""
    __tablename__ = "unanswered_queries"
    
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_query = Column(Text, nullable=False)  # The question
    confidence_score = Column(Float)  # Why it was flagged
    admin_response = Column(Text)  # Admin's manual answer
    ticket_created = Column(String(255))  # Support ticket ID
    status = Column(String(50), default="open")  # open, closed, pending
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Document(Base):
    """Store FAQ documents with vector embeddings"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)  # Document text chunk
    doc_metadata = Column(JSON)  # {"title": "...", "author": "..."}
    embedding = Column(ARRAY(Float), nullable=False)  # Vector embedding as array
    source = Column(String(255))  # Filename: "faqs.pdf"
    doc_type = Column(String(50))  # "faq", "news", "guide", "investment"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
