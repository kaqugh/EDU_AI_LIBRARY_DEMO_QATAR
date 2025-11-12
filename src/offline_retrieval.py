
import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

VECTORS_DIR = "vectors"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
_embedder = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

def _load():
    if os.path.exists(VECTORS_DIR) and any(f.endswith(".faiss") for f in os.listdir(VECTORS_DIR)):
        return FAISS.load_local(VECTORS_DIR, _embedder, allow_dangerous_deserialization=True)
    else:
        print("⚠️ No FAISS index found — running in demo mode.")
        return None

def recommend_for_user(user_name, k=5):
    _vs = _load()
    if not _vs:
        # Demo fallback recommendations
        demo_books = [
            ("الذكاء الاصطناعي في التعليم", 0.91),
            ("الابتكار في تعلم اللغة العربية", 0.87),
            ("أساسيات البرمجة للمدارس", 0.85),
            ("مهارات التفكير النقدي", 0.82),
            ("التعلم الرقمي في قطر", 0.80)
        ]
        return demo_books[:k]
    else:
        query_vector = _embedder.embed_query(user_name)
        results = _vs.similarity_search_with_score(user_name, k=k)
        return [(r.page_content, s) for r, s in results]

def semantic_search_books(query, k=5):
    _vs = _load()
    if not _vs:
        demo_books = [
            ("الذكاء الاصطناعي في التعليم", 0.91),
            ("أساسيات البرمجة للمدارس", 0.85),
            ("مهارات التفكير النقدي", 0.82)
        ]
        return demo_books[:k]
    else:
        results = _vs.similarity_search_with_score(query, k=k)
        return [(r.page_content, s) for r, s in results]
