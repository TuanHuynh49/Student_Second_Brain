import os
from typing import Optional, Tuple, List, Dict, Any
from dotenv import load_dotenv
from groq import Groq
from rich import print

from src.rag.vectordb.VectorStore import VectorStore
from src.models.Query import Query
from src.models.DocumentChunk import RetrievedChunk,ParentChunk
from src.rag.retrieval.Retriever import retrieve
from src.ingestion.chunking.Chunking_helper import loaddoc 

load_dotenv()

RAG_SYSTEM_PROMPT = """You are an intelligent academic assistant for a Student Second Brain system. 
Answer the user's question based ONLY on the following context retrieved from study materials.
If the context does not contain enough information, say: "I cannot find enough information in the provided documents."

Context:
{context}


Question: {question}"""
DECOMPOSE_PROMPT = """Break this answer into individual factual claims.
Return one claim per line. Do not add anything else.

Answer:
{answer}"""

JUDGE_PROMPT = """You are a strict verifier.
Check whether the given claim is SUPPORTED by the context.

Context:
{context}

Claim:
{claim}

Is this claim supported by the context? Answer only "YES" or "NO"."""

class StudentSecondBrainRAG:
    def __init__(self, store: Optional[VectorStore] = None):
       
        self.store = store if store else VectorStore.load()
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY chưa được thiết lập trong file .env")
        self.client = Groq(api_key=api_key)

    def format_retrieved_chunk(self, retrieved_chunk: RetrievedChunk, index: int) -> str:
        parent = ParentChunk()
        parent=retrieved_chunk.parent
        source = parent.source or "None source"
        title = parent.section or "study_document"
        subject = parent.metadata.get("subject", "general")
        
        return f"[{index + 1}] (Môn: {subject} | Nguồn: {source})|Section:{title}\nScore: {retrieved_chunk.score:.4f}\n{parent.content}"

    def build_rag_prompt(self, question: str, retrieved_chunks: list[RetrievedChunk], top_k: int = 3) -> list[dict]:
        context_text = "\n\n---\n\n".join(
            self.format_retrieved_chunk(rc, i) for i, rc in enumerate(retrieved_chunks[:top_k])
        )
        
        system_prompt = RAG_SYSTEM_PROMPT.format(
            context=context_text,
            question=question
        )
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]

    def run(
        self, 
        query_text: str, 
        mode: str = "hybrid", 
        top_k: int = 3, 
        score_threshold: float = 0.0,
        alpha: float = 0.6,
        oversample: int = 4,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[RetrievedChunk]]:
        query = Query(
            text=query_text,
            top_k=top_k,
            score_threshold=score_threshold,
            metadata=metadata or {}
        )
        
        results = retrieve(query, self.store, mode=mode, alpha=alpha, oversample=oversample)
        
        if not results:
            return "I cannot find enough information in the provided documents.", []

        messages = self.build_rag_prompt(query_text, results, top_k=top_k)
        
        try:
            response = self.client.chat.completions.create(
                model="openai/gpt-oss-120b",    
                messages=messages,
                temperature=0.1,         
                max_tokens=1024 
            )
            
            answer = response.choices[0].message.content
            total_tokens = response.usage.total_tokens
            return answer, results,total_tokens
            
        except Exception as e:
            return f"Lỗi khi gọi Groq API: {str(e)}", results


