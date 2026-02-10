# ChatBot_UGF Project Documentation

## Project Overview (Product Management Perspective)

**Project Name:** ChatBot_UGF  
**Role:** AI Engineer / Full Stack Developer (implied)  
**Domain:** FinTech / Private Equity / Venture Capital

### **Problem Statement**
Private Equity and Venture Capital firms manage vast amounts of unstructured proprietary data (investment memos, pitch decks, internal policies). Stakeholders often struggle to quickly retrieve accurate, context-specific information from these documents. Traditional keyword searches fail to capture semantic meaning, and standard Generative AI tools (like ChatGPT) cannot access private data and risk hallucinations or data privacy breaches.

### **Solution: Local RAG (Retrieval-Augmented Generation) Chatbot**
We built a secure, privacy-focused RAG Chatbot that runs entirely locally. It ingests internal documents, understands their semantic meaning, and answers user queries with high precision by referencing specific source material.

### **Key Value Propositions**
1.  **Data Privacy & Compliance:** Zero data leakage. All processing (embedding, inference, storage) happens locally or on-premise, ensuring sensitive financial data never leaves the secure environment.
2.  **Accuracy & Traceability:** Reduces AI hallucinations by grounding answers in retrieved internal facts. It can cite sources, building trust with financial analysts.
3.  **Cost Efficiency:** Eliminates recurring costs of cloud-based LLM APIs (like OpenAI) by leveraging optimized open-source local models (Mistral via Ollama).
4.  **Efficiency:** Reduces research time from hours to seconds by instantly aggregating insights across multiple documents.

---

## System Architecture & Flows

### **1. Data Ingestion Pipeline (The "Knowledge" Build)**
*   **Input:** Multi-format documents (PDFs, Text files) from the firm's knowledge base.
*   **Processing:**
    1.  **Loading:** Documents are parsed using `PyPDFLoader` and `TextLoader`.
    2.  **Chunking:** Text is split into manageable segments (1000 characters) with overlap (200 characters) to preserve context across boundaries using `RecursiveCharacterTextSplitter`.
    3.  **Embedding:** Each chunk is converted into a 384-dimensional vector using the `HuggingFace all-MiniLM-L6-v2` model. This captures the *semantic meaning* of the text, not just keywords.
*   **Storage:** Vectors and metadata are stored in a **PostgreSQL** database optimized with **pgvector** for high-speed similarity search.

### **2. Retrieval & Generation Flow (The User Journey)**
*   **Step 1: User Query:** Analyst asks, *"What is our minimum ticket size for Series A?"*
*   **Step 2: Vector Search:** The system converts the query into a vector and performs a **Cosine Similarity Search** against the database.
*   **Step 3: Retrieval:** The system retrieves the top 3-5 most relevant document chunks (e.g., excerpts from the "Investment Policy 2024" doc).
*   **Step 4: Augmentation:** A prompt is dynamically constructed:
    > *"You are a helpful PE/VC assistant. Answer the question based ONLY on the following context: [Retrieved Chunks]. Question: [User Query]"*
*   **Step 5: Generation:** The prompt is sent to the local LLM (**Mistral** via **Ollama**).
*   **Step 6: Output:** The LLM generates a factual answer synthesized from the chunks.

---

## Technical Stack & Engineering Highlights

| Component | Technology Used | Purpose |
| :--- | :--- | :--- |
| **Backend API** | **FastAPI** (Python) | High-performance, async API for handling chat requests and document processing. |
| **Orchestration** | **LangChain** | Framework for chaining the RAG components (Retriever -> Prompt -> LLM). |
| **LLM Inference** | **Ollama** (running **Mistral**) | Local execution of the Large Language Model. Configured with *Temperature=0.1* for deterministic, factual outputs. |
| **Embeddings** | **HuggingFace** (`all-MiniLM-L6-v2`) | Efficient, compact open-source model for converting text to semantic vectors. |
| **Database** | **PostgreSQL** + **pgvector** | Relational DB extended with vector similarity search capabilities. |
| **Frontend** | **React** (TypeScript) | Modern, responsive UI for the chat interface. |
| **ORM** | **SQLAlchemy** | Database interaction and schema management. |

### **Key Technical Challenges Solved**
*   **Hallucination Control:** Implemented strict prompting ("Answer based ONLY on provided context") and low temperature settings to prevent the AI from making up facts.
*   **Context Quality:** Tuned chunk sizes (1000 chars) and overlap (200 chars) to ensure no critical financial figures were split across chunks, maintaining data integrity.
*   **Local Performance:** Optimized the pipeline to run efficiently on standard hardware by selecting lightweight but powerful embedding models (`all-MiniLM-L6-v2`) and quantized LLMs.
