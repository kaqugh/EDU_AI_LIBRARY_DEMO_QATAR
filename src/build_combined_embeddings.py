
import os, pandas as pd
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

DATA_DIR = "data"
VECTORS_DIR = os.path.join("vectors", "combined_index")
META_CSV = os.path.join("vectors", "combined_meta.csv")
COMBINED_CSV = os.path.join(DATA_DIR, "combined_training.csv")

def main():
    os.makedirs(os.path.dirname(VECTORS_DIR), exist_ok=True)
    df = pd.read_csv(COMBINED_CSV)
    texts = df["text"].tolist()

    embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vs = FAISS.from_texts(texts, embedder)

    df[["id","kind"]].to_csv(META_CSV, index=False, encoding="utf-8")
    vs.save_local(VECTORS_DIR)
    print(f"[OK] Saved FAISS index to {VECTORS_DIR} and meta to {META_CSV}")

if __name__ == "__main__":
    main()
