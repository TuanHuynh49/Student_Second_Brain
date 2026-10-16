from collections import defaultdict
from typing import List, Optional
from src.rag.vectordb.VectorStore import VectorStore
from src.models.DocumentChunk import RetrievedChunk, ChildChunk
from src.models.Query import Query
from src.rag.retrieval.reranker import rerank_chunks

def _process_retrieval(
    query_text: str, 
    candidates: list[tuple[ChildChunk, float]], 
    store: VectorStore, 
    top_k: int
) -> list[RetrievedChunk]:
   
    if not candidates:
        return []
    
    reranked_candidates = rerank_chunks(query_text, candidates)
    
    parent_score = defaultdict(list)
    child_matches = defaultdict(list)
    
    for child, score in reranked_candidates:
        parentId = child.parent_id
        if not parentId:
            continue
        parent_score[parentId].append(score)
        child_matches[parentId].append(child.content)
        
    retrieve_results = []
    for parent_id, scores in parent_score.items():
        parent_obj = store.parent_chunks.get(parent_id)
        if parent_obj:
            best_score = max(scores)  
            retrieve_results.append(
                RetrievedChunk(
                    parent=parent_obj,
                    score=best_score,
                    matched_children=child_matches[parent_id]
                )
            )
            
    retrieve_results.sort(key=lambda x: x.score, reverse=True)
    return retrieve_results[:top_k]


def dense_retrieve(
    query: Query, 
    store: VectorStore, 
    oversample: int = 4
) -> list[RetrievedChunk]:
   
    candidates = store.dense_search(
        query=query.text,
        top_k=query.top_k * oversample,
        score_threshold=query.score_threshold,
        metadata=query.metadata
    )
    return _process_retrieval(query.text, candidates, store, query.top_k)


def hybrid_retrieve(
    query: Query, 
    store: VectorStore, 
    alpha: float = 0.6, 
    oversample: int = 4
) -> list[RetrievedChunk]:
    candidates = store.hybrid_search(
        query=query.text,
        top_k=query.top_k * oversample,
        alpha=alpha,
        score_threshold=query.score_threshold,
        metadata=query.metadata
    )
    return _process_retrieval(query.text, candidates, store, query.top_k)


def retrieve(
    query: Query, 
    store: VectorStore, 
    mode: str = "hybrid", 
    alpha: float = 0.6, 
    oversample: int = 4
) -> list[RetrievedChunk]:

    mode = mode.strip().lower()
    if mode == "dense":
        return dense_retrieve(query, store, oversample=oversample)
    elif mode == "hybrid":
        return hybrid_retrieve(query, store, alpha=alpha, oversample=oversample)
    else:
        raise ValueError(f"Chế độ tìm kiếm không hợp lệ: '{mode}'. Chỉ hỗ trợ 'dense' hoặc 'hybrid'.")