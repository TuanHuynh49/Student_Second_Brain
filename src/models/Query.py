from dataclasses import dataclass, field
@dataclass
class Query:
    text: str
    top_k: int = 5
    
# # src/rag/retriever.py
# from src.models import Query, RetrievedChunk, ParentChunk

# def retrieve(query: Query) -> list[RetrievedChunk]:
#     # TODO: thay bằng Dense/Hybrid retrieval thật
#     return [RetrievedChunk(
#         parent=ParentChunk(content="Nội dung mẫu...", parent_id="x-p0",
#                            doc_id="x", source="lesson_01.pdf", page=3),
#         score=0.9,
#     )]