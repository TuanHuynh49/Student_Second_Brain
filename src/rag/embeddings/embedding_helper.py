from src.rag.embeddings.jina_embeddings import jina_embeddings
import os 
from rich import print 
from dotenv import load_dotenv
import numpy as np 
load_dotenv()
modelemb=os.getenv('MODEL_EMBEDING')
def embed_tex(text: str,model=modelemb ,api_key=None) -> list[float]:
    if api_key is None:
        api_key = os.getenv("JINA_API_KEY")
    
    resp = jina_embeddings(input=text, model=model, api_key=api_key)
    return resp.data[0].embedding

def batch_embed_text(input: list[str], model=modelemb, api_key=None) -> list[list[float]]:
    if api_key is None:
        api_key = os.getenv("JINA_API_KEY")
        
    resp = jina_embeddings(input=input, model=model, api_key=api_key)
    return [item.embedding for item in resp.data]

