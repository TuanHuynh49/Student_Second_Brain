from src.ingestion.embedding.jina_embeddings import jina_embeddings
import os 
from rich import print 
from dotenv import load_dotenv
import numpy as np 
from src.models.VectorStore import VectorStore
from src.models.DocumentChunk import RetrievedChunk
from collections import defaultdict
from src.models.DocumentChunk import RetrievedChunk
from src.ingestion.chunking.Chunking_helper import loaddoc
from src.models.Query import Query

def retrieve(query:Query , store: VectorStore, oversample: int = 4) -> list[RetrievedChunk]:
    hits =store.search(query=query.text,top_k=query.top_k*oversample)
    parent_score=defaultdict(list)
    child_matches=defaultdict(list)
    for child,score in hits:
        parentId=child.parent_id
        if not parentId:
            continue
        parent_score[parentId].append(score)
        child_matches[parentId].append(child.content)
    retrieve_results=[]
    for parent_id,scores in parent_score.items():
        parent_obj=store.parent_chunks.get(parent_id)
        if parent_obj:
            best_score=max(scores)
            retrieve_results.append(
                RetrievedChunk(
                        parent=parent_obj,
                        score=best_score,
                        matched_children=child_matches[parent_id]
                    )
                )
    retrieve_results.sort(key=lambda x: x.score,reverse=True)
    return retrieve_results[:Query.top_k]


    
if __name__ == "__main__":
    myStore = VectorStore()
    res1 = loaddoc("thanhpho.txt")

    res2 = loaddoc("maybay.md")
    if res2 is not None and res1 is not None:
        doc_id = myStore.add(res1)
        doc_id= myStore.add(res2)
        print("--- TEST RETRIEVE (PARENT-CHILD) ---")
        query_str = "Hãy giới thiệu cho tôi về thành phố Hồ Chí Minh như nét đẹp,đặc sản"
        top_k=3
        trv=Query(text=query_str,top_k=top_k)
        results = retrieve(trv, myStore, oversample=3)
        
        for idx, res_chunk in enumerate(results, 1):
            print(f"\n[Kết quả {idx}] Score: {res_chunk.score:.4f}")
            print(f"DocidSection: {res_chunk.parent.doc_id}")
            print(f"Parent Section: {res_chunk.parent.section}")
            print(f"Parent Content (rút gọn): {res_chunk.parent.content[:150]}...")
            print(f"Số lượng matched children: {len(res_chunk.matched_children)}")
    else:
        print("Không tìm thấy file test.txt trong thư mục data/raw/")