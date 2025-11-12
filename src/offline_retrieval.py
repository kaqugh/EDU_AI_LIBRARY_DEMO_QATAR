
import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

VECTORS_DIR = "vectors"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
_embedder = HuggingFaceEmbeddings(model_name=EMBED_MODEL)


def _load():
    """Safely load FAISS index if exists, otherwise return None."""
    try:
        if os.path.exists(VECTORS_DIR):
            faiss_files = [f for f in os.listdir(VECTORS_DIR) if f.endswith(".faiss")]
            if faiss_files:
                print("✅ FAISS index detected, loading vectors...")
                return FAISS.load_local(VECTORS_DIR, _embedder, allow_dangerous_deserialization=True)
        print("⚠️ No FAISS index found — switching to demo mode.")
        return None
    except Exception as e:
        print(f"⚠️ Failed to load FAISS index: {e}")
        return None


def recommend_for_user(user_name, k=5):
    """Return recommended books for user (real FAISS or demo mode)."""
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
        try:
            results = _vs.similarity_search_with_score(user_name, k=k)
            return [(r.page_content, s) for r, s in results]
        except Exception as e:
            print(f"⚠️ FAISS error: {e} — fallback to demo.")
            demo_books = [
                ("الذكاء الاصطناعي في التعليم", 0.91),
                ("الابتكار في تعلم اللغة العربية", 0.87),
                ("أساسيات البرمجة للمدارس", 0.85)
            ]
            return demo_books[:k]


def semantic_search_books(query, k=5):
    """Search for related books in FAISS or demo mode."""
    _vs = _load()
    if not _vs:
        demo_books = [
            ("الذكاء الاصطناعي في التعليم", 0.91),
            ("أساسيات البرمجة للمدارس", 0.85),
            ("مهارات التفكير النقدي", 0.82)
        ]
        return demo_books[:k]
    else:
        try:
            results = _vs.similarity_search_with_score(query, k=k)
            return [(r.page_content, s) for r, s in results]
        except Exception as e:
            print(f"⚠️ Search failed: {e}")
            return [("نتائج تجريبية لعدم توفر قاعدة البيانات", 0.5)]

