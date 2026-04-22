# knowledge/rag_retriever.py

import chromadb
from sentence_transformers import SentenceTransformer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DIR = BASE_DIR / "knowledge" / "rag_store"
COLLECTION_NAME = "chatfarm_tomato_chunks"
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

_model = None
_collection = None


def get_model():
    global _model
    if _model is None:
        print("[RAG] Embedding modeli yükleniyor...")
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def get_collection():
    global _collection
    if _collection is None:
        print("[RAG] Chroma collection bağlanıyor...")
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = client.get_collection(name=COLLECTION_NAME)
    return _collection


def semantic_search(query: str, top_k: int = 5):
    """
    Query embedding üretir ve Chroma'dan en ilgili chunkları döndürür.
    """
    model = get_model()
    collection = get_collection()

    query_embedding = model.encode(
        query,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=top_k,
    )

    chunks = []

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    for doc, meta in zip(documents, metadatas):
        chunks.append({
            "content": doc,
            "metadata": meta,
        })

    return chunks