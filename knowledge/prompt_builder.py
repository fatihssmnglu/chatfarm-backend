# knowledge/prompt_builder.py

from typing import Dict, Any, List


def build_chat_prompt(
    user_message: str,
    sensor_data: Dict[str, Any],
    analysis: Dict[str, Any],
    rag_chunks: List[Dict[str, Any]],
    rag_coverage_ok: bool,
) -> str:
    chunk_texts = []

    for i, chunk in enumerate(rag_chunks, start=1):
        content = chunk.get("content", "")
        metadata = chunk.get("metadata", {})
        chunk_texts.append(
            f"[Kaynak {i}]\n"
            f"İçerik: {content}\n"
            f"Metadata: {metadata}"
        )

    context_text = "\n\n".join(chunk_texts) if chunk_texts else "İlgili kaynak bulunamadı."

    coverage_text = (
        "RAG kaynakları kullanıcı sorusuyla yeterince uyumlu."
        if rag_coverage_ok
        else "RAG kaynakları kullanıcı sorusuyla yeterince uyumlu değil. "
             "Bu durumda kaynak dışı öneri üretme."
    )

    prompt = f"""
Sen bir sera domatesi karar destek asistanısın.

Kurallar:
- SADECE verilen verilere göre konuş.
- RAG kaynakları dışında bilgi kullanma.
- Eğer cevap kaynaklarda yoksa aynen şu ifadeyi kullan: "Bu konuda yeterli veri yok."
- Tahmin yürütme.
- Sensör verisinden tek başına tarımsal öneri türetme.
- Tarımsal öneri verebilmek için ilgili RAG kaynağı veya rule engine çıktısı olmalı.
- Önce mevcut durumu analiz et.
- Sonra nedenini açıkla.
- Sonra öneri ver.
- Cevabı Türkçe ver.
- Kısa ama teknik ol.

KULLANICI SORUSU:
{user_message}

GÜNCEL SENSÖR VERİLERİ:
{sensor_data}

RULE ENGINE ANALİZİ:
{analysis}

RAG KAPSAM DEĞERLENDİRMESİ:
{coverage_text}

SEMANTIC RAG KAYNAKLARI:
{context_text}

Şimdi kullanıcıya doğal, anlaşılır ve teknik olarak tutarlı bir cevap ver.
""".strip()

    return prompt