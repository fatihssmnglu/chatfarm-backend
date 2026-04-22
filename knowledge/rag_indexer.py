# knowledge/rag_indexer.py

import json
from pathlib import Path
from typing import List, Dict, Any

import chromadb
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent.parent
CHUNKS_PATH = BASE_DIR / "dataset" / "chunks.jsonl"
CHROMA_DIR = BASE_DIR / "knowledge" / "rag_store"
COLLECTION_NAME = "chatfarm_tomato_chunks"
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBED_BATCH_SIZE = 32


def load_chunks_from_jsonl(path: Path) -> List[Dict[str, Any]]:
    chunks = []

    with open(path, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                obj = json.loads(line)
                chunks.append(obj)
            except json.JSONDecodeError:
                print(f"[UYARI] JSON parse hatası - satır {line_number}, atlandı.")

    return chunks


def normalize_chunk(chunk: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(chunk.get("id", "")).strip(),
        "content": str(chunk.get("content", "")).strip(),
        "crop": str(chunk.get("crop", "")).strip(),
        "section": str(chunk.get("section", "")).strip(),
        "subsection": str(chunk.get("subsection", "")).strip(),
        "tags": chunk.get("tags", []),
    }


def prepare_documents(chunks: List[Dict[str, Any]]):
    ids = []
    documents = []
    metadatas = []

    for chunk in chunks:
        c = normalize_chunk(chunk)

        if not c["id"] or not c["content"]:
            continue

        ids.append(c["id"])
        documents.append(c["content"])
        metadatas.append(
            {
                "crop": c["crop"],
                "section": c["section"],
                "subsection": c["subsection"],
                "tags": ", ".join(c["tags"]) if isinstance(c["tags"], list) else str(c["tags"]),
            }
        )

    return ids, documents, metadatas


def batch_iter(lst, batch_size):
    for i in range(0, len(lst), batch_size):
        yield lst[i:i + batch_size]


def build_index():
    print("[1/5] chunks.jsonl okunuyor...")
    raw_chunks = load_chunks_from_jsonl(CHUNKS_PATH)
    print(f"Toplam ham chunk sayısı: {len(raw_chunks)}")

    print("[2/5] Chroma klasörü hazırlanıyor...")
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        print(f"[Bilgi] Eski collection siliniyor: {COLLECTION_NAME}")
        client.delete_collection(name=COLLECTION_NAME)

    collection = client.create_collection(name=COLLECTION_NAME)

    print("[3/5] Embedding modeli yükleniyor...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    print("[4/5] Chunklar hazırlanıyor...")
    ids, documents, metadatas = prepare_documents(raw_chunks)
    print(f"Indexlenecek temiz chunk sayısı: {len(ids)}")

    if not ids:
        print("[HATA] Indexlenecek geçerli chunk bulunamadı.")
        return

    print("[5/5] Embedding üretimi ve Chroma insert başlıyor...")

    total_added = 0

    for id_batch, doc_batch, meta_batch in zip(
        batch_iter(ids, EMBED_BATCH_SIZE),
        batch_iter(documents, EMBED_BATCH_SIZE),
        batch_iter(metadatas, EMBED_BATCH_SIZE),
    ):
        embeddings = model.encode(
            doc_batch,
            batch_size=EMBED_BATCH_SIZE,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        collection.add(
            ids=id_batch,
            documents=doc_batch,
            metadatas=meta_batch,
            embeddings=embeddings.tolist(),
        )

        total_added += len(id_batch)
        print(f"Eklenen chunk: {total_added}")

    print("[OK] Semantic RAG index başarıyla oluşturuldu.")


if __name__ == "__main__":
    build_index()