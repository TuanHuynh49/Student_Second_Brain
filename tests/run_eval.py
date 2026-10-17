import os
from dotenv import load_dotenv
from rich import print
from rich.table import Table

from src.rag.pipeline.pipeline import StudentSecondBrainRAG
from src.rag.vectordb.VectorStore import VectorStore
from src.evaluation.evaluator import Evaluator, EvalExample
from src.ingestion.chunking.Chunking_helper import loaddoc

load_dotenv()

def chunking_state1(max_child:int,overlap:int):
    store = VectorStore().load()
    store.clear_all()
    store.save()
    
    res1 = loaddoc("AI_BM25.txt")
    res2 = loaddoc("AI_Programing.txt")
    res3 = loaddoc("AI_React.txt")
    res4 = loaddoc("CAAL.md")
    res5 = loaddoc("DBMS_Nosql.md")
    res6 = loaddoc("DBMS.md")
    res7 = loaddoc("lich_su_viet_nam.md")
    res8 = loaddoc("NetWorking.md")
    res9 = loaddoc("OS.md")
    res10 = loaddoc("toan_hoc_co_ban.md")
    res11 = loaddoc("van_hoc_va_van_hoa_viet_nam.md")
    store.add(res1,'AIP',max_child,overlap)
    store.add(res2,'AIP',max_child,overlap)
    store.add(res3,'AIP',max_child,overlap)
    store.add(res4,'CAAL',max_child,overlap)
    store.add(res5,'DBMS',max_child,overlap)
    store.add(res6,'DBMS',max_child,overlap)
    store.add(res7,'History',max_child,overlap)
    store.add(res8,'NET',max_child,overlap)
    store.add(res9,'OS',max_child,overlap)
    store.add(res10,'Math',max_child,overlap)
    store.add(res11,'Literature',max_child,overlap)
    store.save()

