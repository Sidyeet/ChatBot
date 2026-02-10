# The "Deep Dive": How ChatBot_UGF Actually Works

This document is a comprehensive guide to the inner workings of the ChatBot_UGF system. It explains everything from the high-level concepts (using simple analogies) to the nitty-gritty code execution.

---

## Part 1: The Concept (Explain Like I'm 5)

Imagine you have a new **Junior Analyst** joining your Private Equity firm. Let's call him "**Mistral**".

Mistral is very smart and speaks excellent English, but **he knows nothing about your specific company**. He doesn't know your investment history, your policies, or your active deals.

If you ask Mistral: *"What is our minimum ticket size for Series A?"*, he will stare at you blankly (or guess based on what other firms do).

To fix this, you don't send Mistral back to college. Instead, you give him a **Binder** full of your company's documents.

Now, when you ask the same question:
1.  Mistral opens the **Binder**.
2.  He flips through the pages until he finds the "Investment Guidelines" page.
3.  He reads the paragraph about "Ticket Sizes".
4.  He answers you: *"According to the Investment Guidelines, our minimum is $2M."*

**This process is called RAG (Retrieval-Augmented Generation).**

*   **Retrieval:** Finding the right page in the Binder.
*   **Augmentation:** Giving that page to Mistral along with your question.
*   **Generation:** Mistral reading it and speaking the answer.

In our software:
*   **Mistral** = The AI Model (running locally on your computer).
*   **The Binder** = The Vector Database (PostgreSQL).
*   **You** = The User (Frontend).

---

## Part 2: The "Insides" (Technical Architecture)

Now let's look at the actual engine. This system is built to run **100% locally**, meaning no data ever leaves your computer.

### 1. The Brain: `Ollama` & `Mistral`
*   **What it is:** `Ollama` is a tool that lets us run powerful AI models (like `Mistral`) on a regular laptop.
*   **Role:** It acts as the "mouth" of the operation. It takes text inputs and generates text outputs. It understands grammar, reasoning, and summarization, but relies on us for facts.

### 2. The Translator: `HuggingFace Embeddings`
*   **What it is:** A model (`all-MiniLM-L6-v2`) that translates **Words** into **Numbers**.
*   **Why?** Computers can't understand "meaning" from words. But they are great at math.
*   **The Magic:** It turns the sentence *"Apple"* into a list of numbers (a vector) like `[0.1, 0.5, -0.2]`. It turns *"Fruit"* into `[0.1, 0.4, -0.2]`. Because the numbers are close, the computer knows "Apple" and "Fruit" are related.

### 3. The Memory: `PostgreSQL` + `pgvector`
*   **What it is:** A robust database (like a giant Excel sheet) upgraded with a plugin called `pgvector`.
*   **Role:** It stores the "Number Lists" (vectors) we created above. It allows us to ask: *"Give me the rows where the numbers are mathematically closest to my question's numbers."*

### 4. The Skeleton: `FastAPI` (Python)
*   **What it is:** The control center. It receives requests from the website, talks to the database, talks to the AI, and sends the answer back.

### 5. The Face: `React` (Frontend)
*   **What it is:** The website you see. It handles the chat bubbles, the scrolling, and sending your messages to the Skeleton.

---

## Part 3: The System Flow (Step-by-Step)

Here is exactly what happens, millisecond by millisecond, when the system runs.

### Flow A: "Learning" (Document Ingestion)
*Before you can chat, the system must learn.*

1.  **Upload:** Use the Admin Panel to upload `Investment_Policy.pdf`.
2.  **Extraction:** The system reads the raw text from the PDF.
3.  **Chunking:** The text is too long for the AI to read all at once. We cut it into small "Chunks" (e.g., 1000 characters each).
    *   *Analogy:* cutting a textbook into index cards.
4.  **Embedding:** Each "Chunk" is sent to the **Translator** (HuggingFace). It returns a Vector (384 numbers).
5.  **Storage:** The Text Chunk + The Vector are saved together in the **Database**.

### Flow B: "Reasoning" ( The Chat Loop)
*This is the code in `backend/chat_routes.py`.*

**Step 1: The User Speaks**
*   User types: *"Who is the CEO?"*
*   Frontend sends this text to the Backend API.

**Step 2: Understanding the Question**
*   The Backend sends *"Who is the CEO?"* to the **Translator**.
*   Translator returns a Vector: `[0.9, -0.1, ...]`

**Step 3: The Search (The "Cosine Similarity" Math)**
*   The Database looks at all the stored Vectors.
*   It does a math operation called **Cosine Similarity**. It measures the angle between the Question Vector and every Document Vector.
*   Small angle = High Similarity.
*   It grabs the **Top 5** "Chunks" that are most mathematically similar to the question.

**Step 4: The Prompt Construction**
*   The system pastes those 5 chunks into a strict template:
    > "You are a helpful assistant. Use ONLY the text below to answer the user.
    > Context: [Chunk 1] [Chunk 2] [Chunk 3]...
    > Question: Who is the CEO?"

**Step 5: The "Thinking"**
*   This huge prompt is sent to **Mistral** (via Ollama).
*   Mistral reads the chunks (which contain the CEO's name) and answers:
    > "Based on the documents, the CEO is Sarah Jenkins."

**Step 6: The "Confidence" Check**
*   The system checks how similar the Top 5 chunks actually were.
*   If the similarity score was low (e.g., < 0.6), it flags the conversation as "Requires Admin Attention" because the AI might be guessing or didn't find good info.

**Step 7: The Reply**
*   The answer is sent back to the Frontend and displayed to the user.

---

## Part 4: Why This "Stack" is Special

1.  **Privacy First:**
    *   Most chatbots use OpenAI (ChatGPT). That requires sending your data to OpenAI's servers.
    *   **ChatBot_UGF** uses `Ollama`. The AI lives inside your RAM. If you unplug the internet, **it still works**. This is critical for banks and PE firms.

2.  **"Grounding" (Anti-Hallucination):**
    *   Normal ChatGPT just makes things up if it doesn't know.
    *   Our system uses `Temperature=0.1`. In AI terms, strictness ranges from 0 (Robot) to 1 (Poet). We set it to 0.1 so it strictly adheres to the provided documents.

3.  **Vector Search (Semantic Search):**
    *   Old "Ctrl+F" search looks for exact words. If you search "Money", it won't find "Cash".
    *   **Vector Search** understands that "Money" and "Cash" are close in "meaning space". So if you ask about "Revenue", it will find documents discussing "Sales" and "Income" even if the exact word "Revenue" isn't there.

## Summary Checklist for Resume
*   **Architecture:** RAG (Retrieval Augmented Generation).
*   **Models:** Quantized LLMs (Mistral) + Sentence Transformers (Embeddings).
*   **Backend:** Asynchronous Python (FastAPI).
*   **Database:** Vector Database Implementation (PostgreSQL).
*   **Key Skill:** Translating unstructured data (PDFs) into structured semantic knowledge (Vectors).
