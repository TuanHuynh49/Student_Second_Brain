from sentence_transformers import CrossEncoder
from src.models.DocumentChunk import ChildChunk
from dotenv import load_dotenv
import os 
load_dotenv()

def get_reranker_model() -> CrossEncoder:
    model=os.getenv("MODEL_RERANK")

    _reranker_model = CrossEncoder(model)
    return _reranker_model

def rerank_chunks(query: str, candidates: list[tuple[ChildChunk, float]]) -> list[tuple[ChildChunk, float]]:
    if not candidates:
        return []
    reranker = get_reranker_model()    
    chunks = [chunk for chunk, score in candidates]
    pairs = [(query, chunk.content) for chunk in chunks]
    new_scores = reranker.predict(pairs)
    reranked = sorted(zip(chunks, new_scores), key=lambda x: x[1], reverse=True)
    return [(chunk, float(score)) for chunk, score in reranked]