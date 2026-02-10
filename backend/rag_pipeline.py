from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .config import settings
import json
import logging

logger = logging.getLogger(__name__)

class RAGPipeline:
    """
    Retrieval-Augmented Generation Pipeline
    Handles document loading, embedding, and LLM response generation
    """
    
    def __init__(self):
        """Initialize RAG components"""
        # Embeddings model - converts text to 384-dimensional vectors
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Cloud LLM - Groq API (fast inference, free tier)
        self.llm = ChatGroq(
            model=settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=0.1  # Low temperature = more factual, less creative
        )
        
        # Text splitter - breaks large documents into chunks
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # Characters per chunk
            chunk_overlap=200,  # Overlap for context
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        logger.info(f"RAG Pipeline initialized with Groq model: {settings.GROQ_MODEL}")
    
    def load_pdf(self, file_path: str):
        """Load and process a PDF file into chunks"""
        try:
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            return self.text_splitter.split_documents(documents)
        except Exception as e:
            print(f"Error loading PDF {file_path}: {e}")
            return []
    
    def load_text(self, file_path: str):
        """Load and process a text file into chunks"""
        try:
            loader = TextLoader(file_path, encoding='utf-8')
            documents = loader.load()
            return self.text_splitter.split_documents(documents)
        except Exception as e:
            print(f"Error loading text {file_path}: {e}")
            return []
    
    def create_embeddings(self, text: str):
        """Convert text to embedding vector"""
        try:
            vector = self.embeddings.embed_query(text)
            return vector  # List of 384 floats
        except Exception as e:
            print(f"Error creating embedding: {e}")
            return None
    
    def get_llm_response(self, query: str, context: str) -> str:
        """Get response from Groq LLM with context"""
        prompt = f"""You are a helpful PE/VC firm assistant. Answer the investor's question based ONLY on the provided context. 
If the context doesn't contain relevant information, say "I don't have information about that. Please contact our team."

Context:
{context}

Question: {query}

Answer:"""
        
        try:
            response = self.llm.invoke(prompt)
            # ChatGroq returns an AIMessage object, extract the text content
            return response.content
        except Exception as e:
            print(f"Error getting LLM response: {e}")
            return "I'm having trouble processing your request. Please try again."
    
    def calculate_relevance_score(self, query_embedding: list, doc_embedding: list) -> float:
        """
        Calculate cosine similarity between query and document embeddings
        Returns score between 0.0 and 1.0
        """
        import numpy as np
        try:
            query_vec = np.array(query_embedding)
            doc_vec = np.array(doc_embedding)
            
            # Cosine similarity
            similarity = np.dot(query_vec, doc_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(doc_vec))
            # Convert from -1..1 range to 0..1 range
            return (similarity + 1) / 2
        except Exception as e:
            print(f"Error calculating relevance: {e}")
            return 0.0
