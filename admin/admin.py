"""
Streamlit Admin Dashboard for PE/VC Chatbot
Upload FAQs, manage unanswered queries, view statistics
"""

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, "..", ".env")
load_dotenv(env_path)

st.set_page_config(
    page_title="PE/VC Chatbot Admin",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== Configuration ====================

DATABASE_URL = os.getenv("DATABASE_URL")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change_me")

# ==================== Database Connection ====================

@st.cache_resource
def get_db_connection():
    """Get PostgreSQL connection"""
    try:
        engine = create_engine(DATABASE_URL)
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

# ==================== Authentication ====================

def check_password():
    """Simple password authentication"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("🔐 Admin Access Required")
        password = st.text_input("Enter Admin Password:", type="password")
        
        if password:
            if password == ADMIN_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Incorrect password")
        st.stop()

check_password()

# ==================== Sidebar Navigation ====================

st.sidebar.title("🤖 Chatbot Admin")
page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "❓ Unanswered Queries", "📤 Upload Documents", "⚙️ Settings"]
)

engine = get_db_connection()
if not engine:
    st.error("Cannot connect to database")
    st.stop()

# ==================== Page 1: Dashboard ====================

if page == "📊 Dashboard":
    st.title("📊 Chatbot Analytics Dashboard")
    
    try:
        with engine.connect() as conn:
            # Total queries
            total_queries = conn.execute(
                text("SELECT COUNT(*) FROM chat_messages")
            ).scalar() or 0
            
            # Unanswered queries
            unanswered = conn.execute(
                text("SELECT COUNT(*) FROM unanswered_queries WHERE status='open'")
            ).scalar() or 0
            
            # Total documents
            total_docs = conn.execute(
                text("SELECT COUNT(*) FROM documents")
            ).scalar() or 0
            
            # Average confidence
            avg_conf = conn.execute(
                text("SELECT AVG(confidence_score) FROM chat_messages")
            ).scalar() or 0.0
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Queries", total_queries, "+5 today")
        col2.metric("Unanswered", unanswered, "Needs Action")
        col3.metric("Total Documents", total_docs)
        col4.metric("Avg Confidence", f"{avg_conf*100:.1f}%")
        
        st.divider()
        
        # Recent conversations
        st.subheader("Recent Conversations")
        with engine.connect() as conn:
            df = pd.read_sql(
                text("SELECT user_id, message, response, confidence_score, created_at FROM chat_messages ORDER BY created_at DESC LIMIT 20"),
                conn
            )
        
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No conversations yet")
        
        st.divider()
        
        # Confidence distribution
        st.subheader("Confidence Distribution")
        with engine.connect() as conn:
            confidence_data = pd.read_sql(
                text("""
                SELECT
                    CASE 
                        WHEN confidence_score >= 0.8 THEN 'High (80-100%)'
                        WHEN confidence_score >= 0.6 THEN 'Medium (60-80%)'
                        ELSE 'Low (<60%)'
                    END as category,
                    COUNT(*) as count
                FROM chat_messages
                GROUP BY category
                """),
                conn
            )
        
        if not confidence_data.empty:
            st.bar_chart(confidence_data.set_index('category'))
    
    except Exception as e:
        st.error(f"Error loading dashboard: {e}")

# ==================== Page 2: Unanswered Queries ====================

elif page == "❓ Unanswered Queries":
    st.title("❓ Unanswered Queries")
    st.write("Review and respond to queries with low confidence")
    
    try:
        with engine.connect() as conn:
            df = pd.read_sql(
                text("""
                    SELECT id, user_query, confidence_score, status, created_at
                    FROM unanswered_queries
                    WHERE status = 'open'
                    ORDER BY created_at DESC
                """),
                conn
            )
        
        if not df.empty:
            st.info(f"📋 Found {len(df)} unanswered queries")
            
            for idx, row in df.iterrows():
                with st.expander(f"Query: {row['user_query'][:60]}... | Confidence: {row['confidence_score']:.1%}"):
                    st.write(f"**Query:** {row['user_query']}")
                    st.write(f"**Confidence Score:** {row['confidence_score']:.1%}")
                    st.write(f"**Submitted:** {row['created_at']}")
                    
                    # Admin response form
                    admin_response = st.text_area(
                        "Provide Response:",
                        key=f"response_{row['id']}",
                        height=150,
                        placeholder="Type your response here..."
                    )
                    
                    if st.button("Save Response", key=f"save_{row['id']}"):
                        try:
                            # Update database
                            with engine.begin() as conn:
                                conn.execute(
                                    text("""
                                        UPDATE unanswered_queries
                                        SET admin_response = :response,
                                            status = 'closed',
                                            updated_at = CURRENT_TIMESTAMP
                                        WHERE id = :id
                                    """),
                                    {"response": admin_response, "id": row['id']}
                                )
                            
                            st.success("✅ Response saved!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error saving response: {e}")
        else:
            st.success("✅ All queries have been answered!")
    
    except Exception as e:
        st.error(f"Error loading queries: {e}")

# ==================== Page 3: Upload Documents ====================

elif page == "📤 Upload Documents":
    st.title("📤 Upload Documents")
    st.write("Upload FAQs, investment guides, or news articles to improve chatbot knowledge")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        doc_type = st.selectbox(
            "Document Type",
            ["faq", "investment", "guide", "news"],
            format_func=lambda x: {
                "faq": "FAQ",
                "investment": "Investment Information",
                "guide": "Portal Guide",
                "news": "News Article"
            }[x]
        )
    
    with col2:
        st.write("")  # Spacing
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["pdf", "txt", "md"],
        help="Upload PDF, TXT, or Markdown files"
    )
    
    if uploaded_file is not None:
        file_details = {
            "Filename": uploaded_file.name,
            "FileSize": f"{uploaded_file.size / 1024:.2f} KB",
            "Type": uploaded_file.type
        }
        
        st.info(f"📋 File: {uploaded_file.name}")
        
        if st.button("Upload and Process", type="primary"):
            try:
                st.write("📁 Uploading...")
                
                # Determine MIME type based on file extension
                file_extension = uploaded_file.name.split('.')[-1].lower()
                mime_types = {
                    'pdf': 'application/pdf',
                    'txt': 'text/plain',
                    'md': 'text/markdown'
                }
                mime_type = mime_types.get(file_extension, 'application/octet-stream')
                
                # Create FormData and send to API
                files = {
                    "file": (uploaded_file.name, uploaded_file.getvalue(), mime_type)
                }
                params = {"doc_type": doc_type}
                
                response = requests.post(
                    f"{API_BASE_URL}/admin/upload-document",
                    files=files,
                    params=params,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"✅ Uploaded! Created {result['chunks_created']} document chunks")
                    st.write(f"Source: {result['file']}")
                    st.write(f"Type: {result['document_type']}")
                else:
                    st.error(f"Upload failed: {response.text}")
                    
            except Exception as e:
                st.error(f"Connection error: {e}")

    
    st.divider()
    
    # Recent uploads
    st.subheader("Recent Uploads")
    try:
        with engine.connect() as conn:
            recent = pd.read_sql(
                text("""
                    SELECT DISTINCT source, doc_type, COUNT(*) as chunks, MAX(created_at) as uploaded
                    FROM documents
                    GROUP BY source, doc_type
                    ORDER BY uploaded DESC
                    LIMIT 10
                """),
                conn
            )
        
        if not recent.empty:
            st.dataframe(recent, use_container_width=True, hide_index=True)
        else:
            st.info("No documents uploaded yet")
    except Exception as e:
        st.error(f"Error loading uploads: {e}")

# ==================== Page 4: Settings ====================

elif page == "⚙️ Settings":
    st.title("⚙️ Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("System Information")
        st.write(f"**Database:** PostgreSQL")
        st.write(f"**Vector DB:** pgvector")
        st.write(f"**LLM:** Ollama (Mistral)")
        st.write(f"**API:** http://localhost:8001")
    
    with col2:
        st.subheader("Health Check")
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                st.success(f"✅ API Status: {health['status']}")
                st.write(f"Environment: {health['environment']}")
                st.write(f"Database: {health['database']}")
            else:
                st.error("❌ API is down")
        except:
            st.error("❌ Cannot reach API")
    
    st.divider()
    
    st.subheader("Database Statistics")
    try:
        with engine.connect() as conn:
            stats = {
                "Tables": conn.execute(
                    text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'")
                ).scalar(),
                "Total Messages": conn.execute(
                    text("SELECT COUNT(*) FROM chat_messages")
                ).scalar(),
                "Total Documents": conn.execute(
                    text("SELECT COUNT(*) FROM documents")
                ).scalar(),
            }
        
        for key, value in stats.items():
            st.write(f"**{key}:** {value}")
    except Exception as e:
        st.error(f"Error loading statistics: {e}")

# ==================== Footer ====================

st.sidebar.divider()
st.sidebar.write("© 2025 PE/VC Chatbot Admin")
