from dataclasses import dataclass,field,asdict
from pathlib import * 
from src.models.Document import Document
from src.models.DocumentChunk import ParentChunk,ChildChunk
import json 
from typing import Optional
import re
def loaddoc(filename:str)->Document:
        retrivePath=f"data/raw/{filename}"
        path=Path(retrivePath)
        if not path.exists() or not path.is_file():
            return None
        text=path.read_text(encoding="utf-8")
        return Document(
            content=text,
            source=retrivePath,
            title=path.stem,
            docType=path.suffix
        )
def markdownChunkingParent(doc:Document)->list[ParentChunk]:
    parents=[]
    heading=list(re.finditer(r"^#+.*?$",doc.content,re.MULTILINE))
    doc_content=doc.content
    idx=1
    for i in range(0,len(heading)):
        section=heading[i].group().strip()
        parent_content=""
        if i<len(heading)-1:
            parent_content=doc_content[heading[i].end():heading[i+1].start()].strip()  
                         
        else:             
            parent_content=doc_content[heading[i].end():]
        parent=ParentChunk(doc_id=doc.doc_id,
                                source=doc.source,
                                section=section,
                                parent_index=idx,
                                content=parent_content
                                )
        idx+=1
        parents.append(parent)
    return parents
def normalTextSentenceChunking(doc: Document,max_tk: int = 900,overlap: int = 15) -> list[ParentChunk]:

    parents: list[ParentChunk] = []

    sentences = [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+|\n+", doc.content)
        if s.strip()
    ]

    buffer: list[str] = []
    count = 0
    idx = 1

    for sentence in sentences:

        sentence_len = len(sentence)

        if buffer and count + sentence_len + 1 > max_tk:
            contentreal = " ".join(buffer)

            parent = ParentChunk(
                source=doc.source,
                section=contentreal[:30],
                parent_index=idx,
                content=contentreal,
                doc_id=doc.doc_id
            )

            parents.append(parent)
            idx += 1

            new_buffer = []
            overlap_count = 0

            for old_sentence in reversed(buffer):
                extra = len(old_sentence) + 1

                if overlap_count + extra > overlap:
                    break

                new_buffer.insert(0, old_sentence)
                overlap_count += extra

            buffer = new_buffer
            count = sum(len(s) for s in buffer) + max(0, len(buffer) - 1)

        buffer.append(sentence)

        if len(buffer) == 1:
            count = len(sentence)
        else:
            count += sentence_len + 1

    if buffer:
        contentreal = " ".join(buffer)

        parent = ParentChunk(
            source=doc.source,
            section=contentreal[:30],
            parent_index=idx,
            content=contentreal,
            doc_id=doc.doc_id
        )

        parents.append(parent)

    return parents
def headerCheck(doc: Document) -> bool:
    match = re.search(r"^#+.*?$", doc.content, re.MULTILINE)
    return match is not None
     
def ParentChunking(doc:Document,parent_max:int=1500,parent_overlap:int=150):          
        if doc.docType==".md":
            if headerCheck(doc):
               return markdownChunkingParent(doc)
            else:
                normalTextSentenceChunking(doc)
        elif doc.docType==".txt":
          return normalTextSentenceChunking(doc,parent_max,parent_overlap)
        else:
          return None


def ChildChunking(parent: ParentChunk,child_max: int = 600,child_overlap: int = 80) -> list[ChildChunk]:

    children: list[ChildChunk] = []

    sentences = [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+|\n+", parent.content)
        if s.strip()
    ]

    buffer: list[str] = []
    count = 0

    for sentence in sentences:
        sentence_len = len(sentence)

        if buffer and count + 1 + sentence_len > child_max:
            content = " ".join(buffer)

            child = ChildChunk(
                content=content,
                doc_id=parent.doc_id,
                chunk_index=len(children),
                parent_id= parent.parent_id,
                
            )

            children.append(child)

            new_buffer: list[str] = []
            overlap_count = 0

            for old_sentence in reversed(buffer):
                extra = len(old_sentence) + (1 if new_buffer else 0)

                if overlap_count + extra > child_overlap:
                    break

                new_buffer.insert(0, old_sentence)
                overlap_count += extra

            buffer = new_buffer
            count = len(" ".join(buffer))


        if not buffer and sentence_len > child_max:
            start = 0

            while start < sentence_len:
                piece = sentence[start:start + child_max]

                child = ChildChunk(
                    content=content,
                    doc_id=parent.doc_id,
                    hunk_index=len(children),
                    parent_id= parent.parent_id,
                )

                children.append(child)
                start += max(1, child_max - child_overlap)

            continue

        buffer.append(sentence)
        count = len(" ".join(buffer))

    if buffer:
        content = " ".join(buffer)

        child = ChildChunk(
            content=content,
            doc_id=parent.doc_id,
            chunk_index=len(children),
            parent_id= parent.parent_id,
            
        )

        children.append(child)

    return children
          
          
          
     
