import os
from dotenv import load_dotenv
from rich import print
from rich.table import Table

from src.rag.pipeline.pipeline import StudentSecondBrainRAG
from src.rag.vectordb.VectorStore import VectorStore
from src.evaluation.evaluator import Evaluator, EvalExample
from src.ingestion.chunking.Chunking_helper import loaddoc

load_dotenv()

def chunking_state1():
    store = VectorStore().load()
    store.clear_all()
    store.save()
    res1= loaddoc('w1_lecture_notes.md')
    store.add(res1)
    store.save()

if __name__=="__main__":
    store=VectorStore().load()
    print(len(store.list_all()))
    