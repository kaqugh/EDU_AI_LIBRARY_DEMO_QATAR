
import os, pandas as pd
from typing import List, Tuple
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

VECTORS_DIR = os.path.join("vectors", "combined_index")
META_CSV = os.path.join("vectors", "combined_meta.csv")
BOOKS_CSV = os.path.join("data", "books_dataset.csv")
USERS_CSV = os.path.join("data", "users_profiles.csv")

_embedder = None
_vs = None
_meta = None
_books = None
_users = None

def _load():
    global _embedder, _vs, _meta, _books, _users
    if _embedder is None:
        _embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    if _vs is None:
        _vs = FAISS.load_local(VECTORS_DIR, _embedder, allow_dangerous_deserialization=True)
    if _meta is None:
        _meta = pd.read_csv(META_CSV)
    if _books is None:
        _books = pd.read_csv(BOOKS_CSV)
    if _users is None:
        _users = pd.read_csv(USERS_CSV)

def recommend_for_user(user_name: str, k: int = 5) -> List[Tuple[str, float]]:
    _load()
    query = f"User profile | name: {user_name}"
    docs = _vs.similarity_search_with_score(query, k=50)

    out = []
    for doc, score in docs:
        if "Book | title:" in doc.page_content:
            try:
                title = doc.page_content.split("Book | title:")[1].split("|")[0].strip()
            except:
                title = "Unknown"
            out.append((title, float(score)))
        if len(out) >= k:
            break
    return out

def semantic_search_books(query: str, k: int = 5) -> List[Tuple[str, float]]:
    _load()
    docs = _vs.similarity_search_with_score(f"Book search | {query}", k=100)
    out = []
    for doc, score in docs:
        if "Book | title:" in doc.page_content:
            try:
                title = doc.page_content.split("Book | title:")[1].split("|")[0].strip()
            except:
                title = "Unknown"
            out.append((title, float(score)))
        if len(out) >= k:
            break
    return out
