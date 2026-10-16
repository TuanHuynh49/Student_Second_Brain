import os 
from rich import print 
from dotenv import load_dotenv
import numpy as np 
from rank_bm25 import BM25Okapi
import numpy as np
import sys

def build_bm25_index(chunk_list:list)->BM25Okapi:
    tokenized=[chunk.content.lower().split() for chunk in chunk_list]
    return BM25Okapi(tokenized)
def normalise_scores(scores) -> list[float]:
    scores = list(scores)  
    if not scores:
        return []
    min_s = min(scores)
    max_s = max(scores)
    if max_s == min_s:
        return [1.0] * len(scores)
    return [(s - min_s) / (max_s - min_s) for s in scores]


