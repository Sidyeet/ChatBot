from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from datetime import datetime
import uuid
import json
import os
import tempfile

from .database import get_db, engine, Base
from .models import Document, UnansweredQuery, ChatMessage
from .schemas import DocumentUploadResponse, UnansweredQueryResponse, AdminResponseInput, StatsResponse
from .rag_pipeline import get_rag_pipeline, RAGPipeline
from .migrations import sync_schema

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/upload-document", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = "faq",
    db: Session = Depends(get_db),
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Upload new FAQ/document to knowledge base
    """
    temp_path = None
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            temp_path = tmp_file.name
        
        # Load and process document
        if file.filename.endswith('.pdf'):
            chunks = rag_pipeline.load_pdf(temp_path)
        elif file.filename.endswith(('.txt', '.md')):
            chunks = rag_pipeline.load_text(temp_path)
        else:
            os.remove(temp_path)
            raise ValueError("Unsupported file type. Use PDF or TXT.")
        
        # Process each chunk
        chunks_created = 0
        for chunk in chunks:
            # Create embedding for this chunk
            embedding = rag_pipeline.create_embeddings(chunk.page_content)
            
            if embedding:
                # Safe metadata handling - ensure it's a dict
                metadata = chunk.metadata if isinstance(chunk.metadata, dict) else {}
                
                doc = Document(
                    content=chunk.page_content,
                    doc_metadata=metadata,  # ✅ Fixed: Pass dict directly - SQLAlchemy JSON handles serialization
                    embedding=embedding,  # ✅ Fixed: Pass list directly - pgvector handles conversion
                    source=str(file.filename),  # ✅ Fixed: Convert to string
                    doc_type=str(doc_type)  # ✅ Fixed: Convert to string
                )
                db.add(doc)
                chunks_created += 1
        
        db.commit()
        
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        
        return DocumentUploadResponse(
            status="success",
            file=str(file.filename),
            chunks_created=chunks_created,
            document_type=str(doc_type),
            timestamp=datetime.utcnow()
        )
    
    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        db.rollback()
        print(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.delete("/documents")
async def delete_all_documents(db: Session = Depends(get_db)):
    """Delete all documents from knowledge base"""
    try:
        count = db.query(Document).delete()
        db.commit()
        return {"status": "success", "message": f"Deleted {count} documents", "count": count}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents")
async def get_documents(db: Session = Depends(get_db)):
    """Get list of uploaded documents"""
    try:
        # Group by source to get unique documents
        docs = db.query(
            Document.source, 
            Document.doc_type,
            Document.created_at,
            func.count(Document.id).label("chunk_count")
        ).group_by(
            Document.source, 
            Document.doc_type, 
            Document.created_at
        ).order_by(Document.created_at.desc()).all()
        
        return [
            {
                "source": d.source,
                "doc_type": d.doc_type,
                "created_at": d.created_at,
                "chunk_count": d.chunk_count
            }
            for d in docs
        ]
    except Exception as e:
        print(f"Error fetching documents: {e}")
        return [] # Return empty list on error instead of 500 to avoid breaking UI

@router.get("/unanswered-queries")
async def get_unanswered_queries(db: Session = Depends(get_db)):
    """Get list of unanswered/low-confidence queries for admin review"""
    try:
        queries = db.query(UnansweredQuery).filter(
            UnansweredQuery.status == "open"
        ).order_by(UnansweredQuery.created_at.desc()).all()
        
        return [
            {
                "id": q.id,
                "user_query": q.user_query,
                "confidence_score": q.confidence_score,
                "admin_response": q.admin_response,
                "status": q.status,
                "created_at": q.created_at
            }
            for q in queries
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/respond-query")
async def respond_to_query(
    payload: AdminResponseInput,
    db: Session = Depends(get_db)
):
    """Admin provides response to unanswered query"""
    try:
        query = db.query(UnansweredQuery).filter(
            UnansweredQuery.id == payload.query_id
        ).first()
        
        if not query:
            raise HTTPException(status_code=404, detail="Query not found")
        
        query.admin_response = payload.response
        query.status = "closed"
        query.updated_at = datetime.utcnow()
        db.commit()
        
        # TODO: Add response to knowledge base automatically
        
        return {"status": "success", "query_id": payload.query_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    try:
        total_queries = db.query(ChatMessage).count()
        unanswered = db.query(UnansweredQuery).filter(
            UnansweredQuery.status == "open"
        ).count()
        total_docs = db.query(Document).count()
        
        # Get average confidence
        avg_confidence = db.execute(
            text("SELECT AVG(confidence_score) FROM chat_messages")
        ).scalar() or 0.0
        
        return {
            "total_queries": total_queries,
            "unanswered_count": unanswered,
            "avg_confidence": avg_confidence,
            "total_documents": total_docs,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync-schema")
async def sync_database_schema():
    """
    Manually trigger database schema synchronization
    Adds missing columns to existing tables
    Useful for fixing schema mismatches
    """
    try:
        sync_schema(engine, Base)
        return {
            "status": "success",
            "message": "Database schema synchronized successfully",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schema sync failed: {str(e)}")
