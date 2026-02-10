from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import uuid
import json

from .database import get_db
from .models import ChatMessage, UnansweredQuery, Document
from .schemas import ChatMessageInput, ChatMessageResponse
from .rag_pipeline import get_rag_pipeline, RAGPipeline

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("", response_model=ChatMessageResponse)
async def chat(
    request: ChatMessageInput, 
    db: Session = Depends(get_db),
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Main chat endpoint
    - Receives user question
    - Searches PostgreSQL for similar FAQs
    - Sends to Ollama LLM for response
    - Returns answer with confidence score
    """
    try:
        # Step 1: Create embedding from user question
        query_embedding = rag_pipeline.create_embeddings(request.user_message)
        if not query_embedding:
            raise HTTPException(status_code=500, detail="Failed to create embedding")
        
        # Step 2: Search PostgreSQL -> Client-side Vector Search (Fall-back for when pgvector is missing)
        try:
            # 1. Fetch all documents with their embeddings
            # (Note: For large scale, this should use native PGVECTOR, but we used float array for compatibility)
            all_docs = db.execute(
                text("SELECT id, content, source, doc_type, doc_metadata, embedding FROM documents")
            ).fetchall()
            
            scored_docs = []
            
            if all_docs:
                for doc in all_docs:
                    # embedding is already a float list/array from DB (pg8000 handles float8[])
                    doc_embedding = doc.embedding
                    if doc_embedding:
                        # Calculate similarity using python
                        score = rag_pipeline.calculate_relevance_score(
                            query_embedding, 
                            doc_embedding
                        )
                        if score > 0.6: # configurable threshold
                            scored_docs.append((score, doc))
            
                # Sort by score descending
                scored_docs.sort(key=lambda x: x[0], reverse=True)
                
                # Take top 5
                similar_docs = [doc for score, doc in scored_docs[:5]]
            else:
                similar_docs = []

        except Exception as db_error:
            print(f"Database search error: {db_error}")
            similar_docs = []
        
        # Step 3: Build context from retrieved documents
        context_texts = []
        source_names = []
        
        for doc in similar_docs:
            if doc and doc.content:  # Extract content from row
                context_texts.append(doc.content)
                source_names.append(doc.source if doc.source else "Unknown")
        
        context = "\n\n".join(context_texts) if context_texts else "No relevant FAQ documents found."
        
        # Step 4: Get response from Ollama LLM
        llm_response = rag_pipeline.get_llm_response(
            request.user_message,
            context
        )
        
        # Step 5: Calculate confidence score
        if len(similar_docs) > 0:
            confidence_score = 0.85  # High confidence if documents found
        else:
            confidence_score = 0.3  # Low confidence if no context
        
        requires_attention = confidence_score < 0.7
        
        # Step 6: Log conversation to database
        message_id = str(uuid.uuid4())
        chat_msg = ChatMessage(
            id=message_id,
            user_id=request.user_id,
            message=request.user_message,
            response=llm_response,
            source_documents=json.dumps(source_names),
            confidence_score=confidence_score
        )
        db.add(chat_msg)
        
        # Step 7: Create ticket if low confidence
        if requires_attention:
            ticket = UnansweredQuery(
                id=str(uuid.uuid4()),
                user_query=request.user_message,
                confidence_score=confidence_score,
                status="open"
            )
            db.add(ticket)
        
        db.commit()
        
        return ChatMessageResponse(
            response=llm_response,
            confidence_score=confidence_score,
            sources=source_names,
            requires_attention=requires_attention,
            conversation_id=message_id
        )
    
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
