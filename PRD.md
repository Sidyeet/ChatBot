# Product Requirements Document (PRD): ChatBot_UGF

## 1. Introduction & Vision
**Product Name:** ChatBot_UGF  
**Vision:** To empower Private Equity and Venture Capital firms with a secure, intelligent, and completely private AI assistant that instantly retrieves and synthesizes insights from proprietary internal documents without compromising data security.

## 2. Target Audience
*   **Investment Analysts:** Need to quickly extract data from pitch decks and financial reports.
*   **Principals/Partners:** Need high-level summaries of investment memos and portfolio updates.
*   **Compliance/Legal Officers:** Need fast access to policy documents and regulatory filings.

## 3. Problem Statement
*   **Data Silos:** Critical information is buried in thousands of PDF and text documents, making manual search efficient.
*   **Privacy Risks:** Financial data is highly sensitive. Using public cloud LLMs (like ChatGPT) poses unacceptable data leakage risks.
*   **Hallucinations:** General-purpose AIs often invent facts when asked about specific niche domains.

## 4. Scope
*   **In-Scope:** 
    *   Local hosting of LLM and Vector Database.
    *   Ingestion of PDF, TXT, MD files.
    *   Q&A interface with source citations.
    *   Admin dashboard for document and query management.
*   **Out-of-Scope (MVP):**
    *   Multi-modal inputs (images/charts interpretation).
    *   User authentication/Role Based Access Control (RBAC) - *Deferred to v2*.
    *   Cloud deployment (strictly local for this version).

## 5. Functional Requirements

### 5.1 Core Chat Interface (User-Facing)
*   **FR-01: Natural Language Querying:** Users can ask questions in plain English (e.g., "What is the cap table structure for Project X?").
*   **FR-02: Context-Aware Responses:** The system must answer based *only* on the uploaded documents, refusing to answer irrelevant general knowledge questions to maintain focus.
*   **FR-03: Source Attribution:** Every response must cite the document name(s) used to generate the answer.
*   **FR-04: Conversation History:** The user can see previous interactions in the current session.

### 5.2 Admin Dashboard (Admin-Facing)
*   **FR-05: Document Management:**
    *   Upload interface for PDFs and Text files.
    *   Automatic "chunking" and "embedding" upon upload.
    *   View total document count.
*   **FR-06: Query Analytics:**
    *   Dashboard showing: Total Queries, Unanswered Questions, Average Confidence Score.
*   **FR-07: Unanswered Query Handling:**
    *   List of queries where the AI had low confidence or no data.
    *   Interface for Admins to manually provide the correct answer to these queries to "teach" the system (or close the loop).
*   **FR-08: System Health:** Schema synchronization tools to ensure DB integrity.

### 5.3 AI Engine (Backend)
*   **FR-09: RAG Pipeline:**
    *   **Retrieval:** Use Cosine Similarity to find top 3-5 relevant chunks.
    *   **Augmentation:** Inject chunks into a strict system prompt.
    *   **Generation:** Generate prose answer using local LLM.
*   **FR-10: Fallback Mechanism:** If relevance score is below threshold (e.g., 0.3), return "I don't have enough information in my documents to answer this."

## 6. Non-Functional Requirements
*   **NFR-01: Privacy (Critical):** 100% data locality. No data is sent to OpenAI, Anthropic, or any external server.
*   **NFR-02: Infrastructure Agnostic:** Must run on standard consumer hardware (e.g., MacBook M1/M2/M3 or gaming PC with NVIDIA GPU) using **Ollama**.
*   **NFR-03: Performance:** 
    *   Embedding generation: < 2 seconds per page.
    *   Query response time: < 5 seconds (on recommended hardware).
*   **NFR-04: Scalability:** Support vector store of up to 10,000 document chunks without significant latency degradation.

## 7. Technical Architecture Summary
*   **Frontend:** React + TypeScript (Responsive Web App).
*   **Backend:** FastAPI (Python).
*   **Database:** PostgreSQL + `pgvector` extension.
*   **AI Model:** Mistral-7B (quantized) running via Ollama.
*   **Embeddings:** `all-MiniLM-L6-v2` (HuggingFace).

## 8. Success Metrics (KPIs)
*   **Search Latency:** Average time to first token < 3s.
*   **Deflection Rate:** % of queries answered successfully without human intervention.
*   **Resolution Rate:** % of "Unanswered Queries" resolved by Admins within 24 hours.

## 9. Future Roadmap
*   **v1.1:** Role-Based Access Control (RBAC) to restrict certain docs to Partners only.
*   **v1.2:** Auto-learning loop (Admin responses automatically added to Vector DB).
*   **v1.3:** Citations linking directly to the page number/paragraph in the PDF viewer.
