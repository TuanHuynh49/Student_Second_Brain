from pathlib import Path
import pymupdf
import pymupdf4llm
from src.models.Document import Document
import json 
from dataclasses import dataclass, asdict

def _load_pdf(path:Path)->Document:
    content = pymupdf4llm.to_markdown(str(path))
    with pymupdf.open(path) as pdf:
        pages = [p.get_text().strip() for p in pdf]
    
    return Document(
        content=content,
        title=path.stem,
        source=str(path),
        metadata={"pages":len(pages),"format_init":'pdf'}
    )
def _load_documents(folder:str)-> list[Document]:
    docs=[]
    for path in sorted(Path(folder).rglob("*")):
        if not path.is_file():
            continue
        suffix=path.suffix.lower()

        if suffix==".pdf":
            doc=_load_pdf(path)
        elif suffix in {".md",".txt"}:
            doc=Document(content=path.read_text(encoding="utf-8"),
                         title=path.stem,source=str(path)
                         )
        else:
            continue
        if doc.content.strip():
            docs.append(doc)
    return docs

if __name__=="__main__":
    final=_load_documents('data')
    for doc in final:
        json_string = json.dumps(
        asdict(doc),
        ensure_ascii=False,
        indent=4,
        default=str
        )
        print(json_string)
        
    

    
