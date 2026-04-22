# knowledge/rag_pipeline.py

from typing import Dict, Any, List

from knowledge.rag_retriever import semantic_search


def detect_topic(user_message: str) -> str:
    """
    Kullanıcı sorusunun ana konusunu kaba olarak tespit eder.
    Bu sayede retrieval sonrası topic filter uygulayabiliriz.
    """
    message = user_message.lower()

    if (
        "toprak" in message
        or "nem" in message
        or "soil" in message
        or "moisture" in message
        or "sulama" in message
        or "su" in message
    ):
        return "soil"

    elif (
        "sıcak" in message
        or "sicak" in message
        or "ısı" in message
        or "isi" in message
        or "temperature" in message
    ):
        return "temperature"

    elif (
        "ışık" in message
        or "isik" in message
        or "light" in message
    ):
        return "light"

    elif (
        "nem oranı" in message
        or "hava nemi" in message
        or "humidity" in message
    ):
        return "humidity"

    return "general"


def build_rag_query(
    user_message: str,
    sensor_data: Dict[str, Any] | None = None,
    analysis: Dict[str, Any] | None = None,
) -> str:
    """
    Kullanıcı mesajı + sensör verisi + rule engine çıktısını
    semantic retrieval için tek bir metin sorgusuna dönüştürür.
    """

    sensor_data = sensor_data or {}
    analysis = analysis or {}

    parts = []

    # 1) Kullanıcı sorusu
    parts.append(f"Kullanıcı sorusu: {user_message}")

    # 2) Sensör özeti
    if sensor_data:
        sensor_lines = []
        for key, value in sensor_data.items():
            sensor_lines.append(f"{key}: {value}")
        parts.append("Güncel sensör verileri: " + ", ".join(sensor_lines))

    # 3) Rule engine özeti
    matched_rules = analysis.get("matched_rules", [])
    effects = analysis.get("effects", [])
    actions = analysis.get("actions", [])
    status = analysis.get("status", "")

    if status:
        parts.append(f"Analiz durumu: {status}")

    if matched_rules:
        rule_texts = []
        for rule in matched_rules:
            crop = rule.get("crop", "")
            condition = rule.get("condition", "")
            effect = rule.get("effect", "")
            action = rule.get("action", "")
            rule_texts.append(
                f"crop={crop}, condition={condition}, effect={effect}, action={action}"
            )
        parts.append("Tetiklenen kurallar: " + " | ".join(rule_texts))

    if effects:
        parts.append("Beklenen etkiler: " + ", ".join(map(str, effects)))

    if actions:
        parts.append("Önerilen aksiyonlar: " + ", ".join(map(str, actions)))

    return "\n".join(parts)


def filter_chunks_by_topic(chunks: List[Dict[str, Any]], topic: str) -> List[Dict[str, Any]]:
    """
    Semantic search sonrası kaba topic filter uygular.
    Amaç: yanlış konu chunk'larının LLM'e gitmesini azaltmak.
    """

    if topic == "general":
        return chunks[:5]

    topic_keywords = {
        "soil": [
            "toprak",
            "nem",
            "soil",
            "moisture",
            "sulama",
            "su stresi",
            "kök",
        ],
        "temperature": [
            "sıcak",
            "sicak",
            "ısı",
            "isi",
            "temperature",
            "gece sıcaklığı",
            "gündüz sıcaklığı",
        ],
        "light": [
            "ışık",
            "isik",
            "light",
            "güneş",
            "radyasyon",
        ],
        "humidity": [
            "nem",
            "humidity",
            "bağıl nem",
            "bagil nem",
            "hava nemi",
        ],
    }

    keywords = topic_keywords.get(topic, [])

    filtered = []

    for chunk in chunks:
        content = chunk.get("content", "").lower()
        metadata = chunk.get("metadata", {})

        metadata_text = " ".join(
            str(v).lower() for v in metadata.values()
        )

        combined_text = f"{content} {metadata_text}"

        if any(keyword in combined_text for keyword in keywords):
            filtered.append(chunk)

    # Eğer filter sonrası hiç chunk kalmazsa tamamen boş dönmeyelim.
    # Fallback olarak ilk 3 semantic sonucu döndür.
    if not filtered:
        return chunks[:3]

    return filtered[:5]


def get_rag_context(
    user_message: str,
    sensor_data: Dict[str, Any] | None = None,
    analysis: Dict[str, Any] | None = None,
    top_k: int = 5,
) -> Dict[str, Any]:
    """
    Semantic RAG için birleşik sorgu üretir ve en ilgili chunkları döner.
    """

    rag_query = build_rag_query(
        user_message=user_message,
        sensor_data=sensor_data,
        analysis=analysis,
    )

    topic = detect_topic(user_message)

    # Önce geniş çekiyoruz, sonra topic filter uyguluyoruz
    raw_chunks = semantic_search(rag_query, top_k=10)
    chunks = filter_chunks_by_topic(raw_chunks, topic)[:top_k]

    return {
        "topic": topic,
        "rag_query": rag_query,
        "chunks": chunks,
    }