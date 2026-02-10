-- Enable pgvector extension (OPTIONAL - Skipped for now)
-- CREATE EXTENSION IF NOT EXISTS vector;

-- Table 1: Store chat conversations
CREATE TABLE IF NOT EXISTS chat_messages (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    source_documents TEXT,
    confidence_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 2: Track unanswered queries for admin review
CREATE TABLE IF NOT EXISTS unanswered_queries (
    id VARCHAR(255) PRIMARY KEY,
    user_query TEXT NOT NULL,
    confidence_score FLOAT,
    admin_response TEXT,
    ticket_created VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'open'
);

-- Table 3: Store FAQ documents with standard array embeddings
CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    doc_metadata JSONB,
    embedding FLOAT8[],  -- Standard Postgres Array
    source VARCHAR(255),
    doc_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created ON chat_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_unanswered_queries_created ON unanswered_queries(created_at);
CREATE INDEX IF NOT EXISTS idx_unanswered_queries_status ON unanswered_queries(status);
CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source);
CREATE INDEX IF NOT EXISTS idx_documents_doc_type ON documents(doc_type);
-- Index for vector search removed (ivfflat requires pgvector)

-- Verify tables were created
SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;
