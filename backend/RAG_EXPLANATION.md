# Complete Guide to RAG (Retrieval-Augmented Generation) Pipeline

## What is RAG?

**RAG (Retrieval-Augmented Generation)** is a technique that combines two powerful AI concepts:
1. **Retrieval**: Finding relevant information from a knowledge base (like your documents)
2. **Augmented Generation**: Using a Large Language Model (LLM) to generate answers based on that retrieved information

Think of it like this: Instead of asking an AI to answer from its training data (which might be outdated or not specific to your needs), RAG:
- First searches YOUR documents for relevant information
- Then gives that information to the AI along with the question
- The AI generates an answer based on YOUR specific documents

This is perfect for chatbots that need to answer questions about specific company documents, policies, or knowledge bases.

---

## The RAG Pipeline - Step by Step

### 1. **Document Loading** (Lines 36-54)

**What happens**: Your PDF or text files are loaded and broken into smaller pieces called "chunks"

**Keywords defined**:
- **PDF (Portable Document Format)**: A file format for documents that preserves formatting
- **Text Splitter**: A tool that breaks long documents into smaller pieces
- **Chunks**: Small pieces of text (usually 500-2000 characters) that are easier to process
- **Encoding**: How text is represented in bytes (UTF-8 is the standard for most languages)

**Why chunk documents?**
- LLMs have limits on how much text they can process at once
- Smaller chunks make it easier to find the most relevant information
- It's more efficient to search through many small pieces than one huge document

**Example**: A 50-page PDF might be split into 200 chunks of ~1000 characters each.

---

### 2. **Embeddings** (Lines 17-20, 56-63)

**What happens**: Text is converted into mathematical vectors (arrays of numbers) that represent meaning

**Keywords defined**:
- **Embedding**: A mathematical representation of text as a list of numbers (vector)
- **Vector**: An array of numbers (like [0.1, -0.3, 0.7, ...]) that represents meaning
- **HuggingFace**: A company/platform that provides pre-trained AI models
- **all-MiniLM-L6-v2**: A specific embedding model that converts text to 384-dimensional vectors
- **384-dimensional**: The vector has 384 numbers in it (each number represents some aspect of meaning)
- **Device**: Where computation happens ('cpu' = your computer's processor, 'gpu' = graphics card for faster processing)

**How embeddings work**:
- Similar words/sentences get similar vectors
- "Investment" and "funding" would have vectors that are close together
- "Investment" and "banana" would have vectors far apart
- This allows computers to understand semantic similarity mathematically

**Example**:
```
"PE firm invests in startups" → [0.2, -0.1, 0.5, 0.3, ...] (384 numbers)
"Venture capital funding" → [0.19, -0.12, 0.48, 0.31, ...] (very similar!)
"Buy groceries" → [-0.3, 0.8, -0.2, 0.1, ...] (very different!)
```

---

### 3. **Text Splitting** (Lines 30-34)

**What happens**: Documents are intelligently broken into overlapping chunks

**Keywords defined**:
- **RecursiveCharacterTextSplitter**: A smart text splitter that tries to break text at natural boundaries
- **Chunk size**: Maximum characters per chunk (1000 in your code)
- **Chunk overlap**: Characters that are repeated between chunks (200 in your code)
- **Separators**: Characters/strings where it's safe to split (newlines, periods, spaces)

**Why overlap?**
- If a sentence spans two chunks, overlap ensures context isn't lost
- Example: Chunk 1 ends with "The investment was..." and Chunk 2 starts with "...$10 million"
- With overlap, both chunks contain the full context

**Example**:
```
Original: "Our firm specializes in Series A funding. We typically invest $2-5M..."
Chunk 1: "Our firm specializes in Series A funding. We typically invest $2-5M..."
Chunk 2: "...invest $2-5M in early-stage startups. Our portfolio includes..."
```

---

### 4. **LLM (Large Language Model)** (Lines 23-27, 65-82)

**What happens**: A language model generates human-like responses based on prompts

**Keywords defined**:
- **LLM (Large Language Model)**: An AI model trained on massive amounts of text to understand and generate language
- **Ollama**: A tool that lets you run LLMs locally on your computer (instead of using cloud APIs)
- **Mistral**: A specific LLM model (like GPT but open-source and can run locally)
- **Temperature**: Controls randomness in responses (0.1 = very focused/factual, 1.0 = more creative/random)
- **Base URL**: The address where Ollama is running (localhost:11434 = your own computer)
- **Prompt**: The text you send to the LLM with instructions and context
- **Invoke**: The method to send a prompt to the LLM and get a response

**Why low temperature (0.1)?**
- For factual answers from documents, you want consistency
- Low temperature = same question gets similar answers
- High temperature = more creative but less reliable for facts

**The prompt structure**:
```
1. Role: "You are a helpful PE/VC firm assistant"
2. Instructions: "Answer based ONLY on provided context"
3. Context: The relevant document chunks
4. Question: The user's query
5. Request: "Answer:"
```

---

### 5. **Relevance Scoring** (Lines 84-100)

**What happens**: Calculates how similar a document chunk is to the user's question

**Keywords defined**:
- **Relevance Score**: A number (0.0 to 1.0) showing how similar two pieces of text are
- **Cosine Similarity**: A mathematical way to measure similarity between two vectors
- **NumPy**: A Python library for mathematical operations on arrays/vectors
- **Dot Product**: Multiplying corresponding elements of two vectors and summing them
- **Norm (Magnitude)**: The "length" of a vector (distance from origin)

**How cosine similarity works**:
1. Convert both query and document to embeddings (vectors)
2. Calculate the angle between the two vectors
3. Similar vectors point in similar directions (small angle = high similarity)
4. Convert from -1 to 1 range (cosine) to 0 to 1 range (relevance score)

**Example**:
```
Query: "What is your investment strategy?"
Doc 1: "Our investment strategy focuses on Series A..." → Score: 0.92 (very relevant!)
Doc 2: "Contact us at info@firm.com..." → Score: 0.15 (not relevant)
```

---

## How Everything Works Together

### The Complete RAG Flow:

1. **User asks a question**: "What is your minimum investment size?"

2. **Convert question to embedding**: 
   - Question → Vector [0.1, -0.2, 0.5, ...]

3. **Search for relevant chunks**:
   - Compare question embedding with all document chunk embeddings
   - Find chunks with highest relevance scores (e.g., top 3-5 chunks)

4. **Retrieve context**:
   - Get the actual text from the most relevant chunks
   - Combine them into a context string

5. **Generate answer**:
   - Send prompt to LLM with: role + instructions + context + question
   - LLM generates answer based on the retrieved context
   - Return answer to user

### Example Flow:

```
User: "What is your investment range?"

Step 1: Embed question → [0.2, -0.1, 0.4, ...]

Step 2: Compare with all document chunks:
  - Chunk 1: "We invest $2M-$10M in Series A" → Score: 0.95 ✓
  - Chunk 2: "Our team has 20 years experience" → Score: 0.23 ✗
  - Chunk 3: "Investment range varies by stage" → Score: 0.87 ✓

Step 3: Retrieve top chunks:
  Context = "We invest $2M-$10M in Series A. Investment range varies by stage."

Step 4: Send to LLM:
  Prompt: "You are a helpful assistant. Answer based on: 
           'We invest $2M-$10M in Series A. Investment range varies by stage.'
           Question: What is your investment range?"

Step 5: LLM generates:
  Answer: "Based on our documents, we typically invest between $2 million 
           and $10 million in Series A funding rounds. The specific range 
           may vary depending on the investment stage."
```

---

## Key Benefits of RAG

1. **Up-to-date information**: Uses your current documents, not outdated training data
2. **Domain-specific**: Answers based on YOUR company's information
3. **Transparent**: Can show which documents were used (source citations)
4. **Private**: Everything runs locally, no data sent to external APIs
5. **Cost-effective**: No per-query costs like cloud APIs

---

## Technical Terms Summary

- **RAG**: Retrieval-Augmented Generation
- **Embedding**: Converting text to numbers (vectors)
- **Vector**: Array of numbers representing text meaning
- **Chunk**: Small piece of a document
- **LLM**: Large Language Model (AI that generates text)
- **Ollama**: Tool to run LLMs locally
- **Temperature**: Controls randomness in AI responses
- **Cosine Similarity**: Mathematical measure of similarity
- **Relevance Score**: How similar two pieces of text are (0-1)
- **Prompt**: Instructions and context sent to LLM
- **RecursiveCharacterTextSplitter**: Smart text chunking tool
- **HuggingFace**: Platform with pre-trained AI models

---

## Why This Architecture?

This RAG pipeline is designed for a **PE/VC (Private Equity/Venture Capital) firm chatbot** that:
- Answers investor questions about the firm
- Uses internal documents (pitch decks, policies, portfolio info)
- Provides accurate, document-based answers
- Runs privately (no cloud dependencies for sensitive financial data)

The low temperature (0.1) ensures factual, consistent answers rather than creative responses, which is crucial for financial/investment information.

