from dataclasses import dataclass, field, asdict
from pathlib import *
from src.models.Document import Document
from src.models.DocumentChunk import ParentChunk, ChildChunk
import json
from typing import Optional
import re
from datetime import datetime
from dotenv import load_dotenv
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Optional
from src.models.Document import Document
from src.models.DocumentChunk import ParentChunk, ChildChunk
load_dotenv()

def extract_markdown_metadata(content: str) -> dict:
    metadata = {}
    
    header_part = content.split("---")[0] if "---" in content else content[:1000]
    
    course_match = re.search(r"\*\*Course:\*\*\s*(.+)", header_part)
    if course_match:
        metadata["course"] = course_match.group(1).strip()
    
    week_match = re.search(r"\*\*Week:\*\*\s*(.+)", header_part)
    if week_match:
        metadata["week"] = week_match.group(1).strip()
        
    prereq_match = re.search(r"\*\*Prerequisites:\*\*\s*(.+)", header_part)
    if prereq_match:
        metadata["prerequisites"] = prereq_match.group(1).strip()
    return metadata
def loaddoc(filename: str) -> Optional[Document]:
    base = os.getenv("DOC_PATH")
    if not base:
        raise ValueError("DOC_PATH chưa được thiết lập trong file .env")

    path = Path(base) / filename
    if not path.exists() or not path.is_file():
        return None

    text = path.read_text(encoding="utf-8")
    doc_metadata = {"docType": path.suffix}
    if path.suffix == ".md":
        doc_metadata.update(extract_markdown_metadata(text))

    return Document(
        content=text,
        source=str(path),
        title=path.stem,
        metadata=doc_metadata,
    )
def markdownChunkingParent(doc: Document) -> list[ParentChunk]:
    parents = []
    heading = list(re.finditer(r"^#+.*?$", doc.content, re.MULTILINE))
    doc_content = doc.content
    idx = 1
    for i in range(0, len(heading)):
        section = heading[i].group().strip()
        parent_content = ""
        if i < len(heading) - 1:
            parent_content = doc_content[heading[i].end():heading[i + 1].start()].strip()
        else:
            parent_content = doc_content[heading[i].end():]
        parent = ParentChunk(
            doc_id=doc.doc_id,
            source=doc.source,
            section=section,
            parent_index=idx,
            content=parent_content,
        )
        idx += 1
        parents.append(parent)
    return parents


def normalTextSentenceChunking(doc: Document, max_tk: int = 900, overlap: int = 15) -> list[ParentChunk]:

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
                doc_id=doc.doc_id,
                metadata={**doc.metadata, "parentSize": len(contentreal)},
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
            doc_id=doc.doc_id,
            metadata={**doc.metadata, "parentSize": len(contentreal)},
        )

        parents.append(parent)

    return parents


def headerCheck(doc: Document) -> bool:
    match = re.search(r"^#+.*?$", doc.content, re.MULTILINE)
    return match is not None


def ParentChunking(doc: Document, parent_max: int = 1500, parent_overlap: int = 150):
    doc_type = doc.metadata.get("docType")
    if doc_type == ".md":
        if headerCheck(doc):
            return markdownChunkingParent(doc)
        return normalTextSentenceChunking(doc, parent_max, parent_overlap)
    elif doc_type == ".txt":
        return normalTextSentenceChunking(doc, parent_max, parent_overlap)
    return None


def ChildChunking(
    parent: ParentChunk,
    child_max: int = 600,
    child_overlap: int = 80,
) -> list[ChildChunk]:

    children: list[ChildChunk] = []

    if child_max <= 0:
        raise ValueError("child_max must be > 0")

    if not 0 <= child_overlap < child_max:
        raise ValueError("Invalid child_overlap")

    sentences = [
        s.strip()
        for s in re.split(
            r"(?<=[.!?])\s+|\n+",
            parent.content,
        )
        if s.strip()
    ]

    buffer: list[str] = []
    count = 0

    # ===== LỖI 3: datetime -> isoformat =====
    def save_child(content: str) -> None:
        child = ChildChunk(
            content=content,
            doc_id=parent.doc_id,
            chunk_index=len(children),
            parent_id=parent.parent_id,
            metadata={
                "create_date": datetime.now().isoformat(),
                "size": len(content),
            },
        )
        children.append(child)

    for sentence in sentences:
        sentence_len = len(sentence)

        # Xử lý câu dài hơn giới hạn
        if sentence_len > child_max:
            if buffer:
                save_child(" ".join(buffer))
                buffer = []
                count = 0

            start = 0
            step = child_max - child_overlap

            while start < sentence_len:
                piece = sentence[start:start + child_max]
                save_child(piece)
                start += step

            continue

        # Nếu thêm câu mới vượt giới hạn
        if buffer and count + 1 + sentence_len > child_max:
            save_child(" ".join(buffer))

            # Giữ các câu cuối để tạo overlap
            new_buffer: list[str] = []
            overlap_count = 0

            for old_sentence in reversed(buffer):
                extra = len(old_sentence) + (
                    1 if new_buffer else 0
                )

                if overlap_count + extra > child_overlap:
                    break

                new_buffer.insert(0, old_sentence)
                overlap_count += extra

            buffer = new_buffer
            count = len(" ".join(buffer))

            # Không để chunk vượt quá child_max
            if buffer and count + 1 + sentence_len > child_max:
                buffer = []
                count = 0

        buffer.append(sentence)
        count = len(" ".join(buffer))

    # Lưu phần còn lại
    if buffer:
        save_child(" ".join(buffer))

    return children