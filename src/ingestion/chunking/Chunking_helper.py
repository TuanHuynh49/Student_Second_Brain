import hashlib
import json
import re
from pathlib import Path
from dataclasses import asdict
from src.models.Document import Document
from src.models.DocumentChunk import ParentChunk, ChildChunk
from src.ingestion.chunking.loader import _load_documents
HEADING = re.compile(r"^#{1,4}\s+(.*)$", re.MULTILINE)
SENTENCE = re.compile(r"(?<=[.!?])\s+|\n+")

def make_doc_id(source: str) -> str:
    return hashlib.md5(source.encode()).hexdigest()[:12]
#--parent set up --
def chunk_document(doc: Document, parent_max=1800, child_size=600, child_overlap=80):
    if not doc.doc_id:
        doc.doc_id = make_doc_id(doc.source)
        
    parents = split_parents(doc, parent_max)
    children = [c for p in parents for c in split_children(p, child_size, child_overlap)]
    return parents, children


def split_parents(doc: Document, max_chars=1800) -> list[ParentChunk]:
    pages_data = doc.metadata.get("pages")
    if isinstance(pages_data, list) and pages_data:
        regions = [(text, i + 1, "") for i, text in enumerate(pages_data) if text.strip()]
    else:
        regions = [(body, None, title) for title, body in _split_by_heading(doc)]

    parents: list[ParentChunk] = []
    for text, page, section in regions:
        for piece in _pack_paragraphs(text, max_chars):
            idx = len(parents)
            parents.append(ParentChunk(
                content=piece,
                parent_id=f"{doc.doc_id}-p{idx}",
                doc_id=doc.doc_id,
                source=doc.source,
                page=page,
                section=section or doc.title,
                parent_index=idx,
            ))
    return parents


def _split_by_heading(doc: Document):
    text = doc.content
    matches = list(HEADING.finditer(text))
    if not matches:
        return [(doc.title, text)]
        
    out = []
    if text[:matches[0].start()].strip():
        out.append((doc.title, text[:matches[0].start()]))
        
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((m.group(1).strip(), text[m.start():end]))
        
    return out


def _pack_paragraphs(text: str, max_chars: int) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    pieces, buf = [], ""
    for p in paras:
        if buf and len(buf) + len(p) + 2 > max_chars:
            pieces.append(buf)
            buf = p
        else:
            buf = f"{buf}\n\n{p}" if buf else p
    if buf:
        pieces.append(buf)
    return pieces

#--child set up---
def split_children(parent: ParentChunk, size=600, overlap=80) -> list[ChildChunk]:
    sentences = [s.strip() for s in SENTENCE.split(parent.content) if s.strip()]
    children: list[ChildChunk] = []
    buf: list[str] = []

    for s in sentences:
        if buf and len(" ".join(buf)) + len(s) + 1 > size:
            j = len(children)
            children.append(ChildChunk(
                content=" ".join(buf),
                chunk_id=f"{parent.parent_id}-c{j}",
                parent_id=parent.parent_id,
                doc_id=parent.doc_id,
                chunk_index=j,
                metadata={
                    "source": parent.source, 
                    "page": parent.page,
                    "section": parent.section
                },
            ))
            
            keep, n = [], 0
            for t in reversed(buf):
                if n + len(t) > overlap:
                    break
                keep.insert(0, t)
                n += len(t)
            buf = keep
            
        buf.append(s)

    if buf:
        j = len(children)
        children.append(ChildChunk(
            content=" ".join(buf),
            chunk_id=f"{parent.parent_id}-c{j}",
            parent_id=parent.parent_id,
            doc_id=parent.doc_id,
            chunk_index=j,
            metadata={
                "source": parent.source, 
                "page": parent.page,
                "section": parent.section
            },
        ))
        
    return children


# ----------Test----------
if __name__ == "__main__":
    final = _load_documents('data')
    print(f"\n[INFO] Tổng số tài liệu đã nạp thành công: {len(final)}\n")
    
    for doc in final:
        parents, children = chunk_document(doc)
        all_output_data = []
        doc_data = {
            "document_title": doc.title,
            "doc_id": doc.doc_id,
            "source": doc.source,
            "total_parents": len(parents),
            "total_children": len(children),
            "parents_sample": [asdict(p) for p in parents],
            "children_sample": [asdict(c) for c in children]
        }
        
        all_output_data.append(doc_data)
    output_file = Path("output_chunks.json")
    output_file.write_text(
        json.dumps(all_output_data, ensure_ascii=False, indent=4, default=str),
        encoding="utf-8"
    )