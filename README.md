# Student_Second_Brain
from src.models import Query, RetrievedChunk, ParentChunk

def retrieve(query: Query) -> list[RetrievedChunk]:
    # TODO: thay bằng Dense/Hybrid retrieval thật
    return [RetrievedChunk(
        parent=ParentChunk(content="Nội dung mẫu...", parent_id="x-p0",
                           doc_id="x", source="lesson_01.pdf", page=3),
        score=0.9,
    )]