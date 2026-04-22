from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response

from telemetry.models import Measurement
from knowledge.services import generate_advice
from knowledge.rag_pipeline import get_rag_context
from knowledge.prompt_builder import build_chat_prompt
from knowledge.llm_service import generate_llm_answer


def chat_page(request):
    return render(request, "chatbot/chat.html")


@api_view(["POST"])
def chat_api(request):
    # Kullanıcının şu an yazdığı mesaj
    message = request.data.get("message", "").strip()

    # Frontend'den gelen konuşma geçmişi
    history = request.data.get("history", [])

    if not message:
        return Response(
            {
                "message": "",
                "answer": "Mesaj boş olamaz."
            },
            status=400
        )

    # Session içinde önceki analizleri tutuyoruz
    last_analysis = request.session.get("last_analysis")
    last_sensor_data = request.session.get("last_sensor_data")
    last_answer = request.session.get("last_answer")
    last_topic = request.session.get("last_topic")
    last_rag_query = request.session.get("last_rag_query")

    # En son sensör verisini al
    latest_measurement = Measurement.objects.order_by("-created_at").first()

    if not latest_measurement and not last_sensor_data:
        return Response(
            {
                "message": message,
                "answer": "Henüz sensör verisi bulunmuyor."
            },
            status=404
        )

    # Yeni veri varsa onu kullan, yoksa session'daki son veriyi kullan
    if latest_measurement:
        sensor_data = {
            "temperature": latest_measurement.temperature,
            "humidity": latest_measurement.humidity,
            "soil_moisture": latest_measurement.soil_moisture,
            "light": latest_measurement.light,
        }
    else:
        sensor_data = last_sensor_data

    # Bu anlık sensör verisine göre analysis üret
    advice_result = generate_advice(sensor_data)

    message_lower = message.lower()

    # Selamlaşma tespiti
    is_greeting = (
        "merhaba" in message_lower
        or "selam" in message_lower
        or "hello" in message_lower
        or "hi" in message_lower
    )

    # Durum / mevcut analiz isteği
    is_status = (
        "durum" in message_lower
        or "şu an" in message_lower
        or "su an" in message_lower
        or "risk" in message_lower
        or "mevcut" in message_lower
        or "analiz" in message_lower
    )

    # Neden sorusu
    is_reason = (
        "neden" in message_lower
        or "niye" in message_lower
        or "hangi sebeple" in message_lower
    )

    # Takip / devam sorusu
    is_follow_up = any(expr in message_lower for expr in [
        "bu durumda",
        "ne yapmam lazım",
        "ne yapmalıyım",
        "nasıl engellerim",
        "nasıl önlerim",
        "bunu nasıl engellerim",
        "bunu nasıl önlerim",
        "buna karşı",
        "peki şimdi",
        "peki ne yapayım",
        "şimdi ne yapayım",
        "ne önerirsin",
        "bunu düzeltmek için",
        "bu konu",
        "bu konuda"
    ])

    # Kısa takip sorularında önceki user mesajını bağlama ekle
    contextual_message = message

    if is_follow_up and history:
        previous_user_messages = [
            item.get("content", "").strip()
            for item in history[:-1]  # Son eleman bazen şu anki mesaj olabiliyor
            if item.get("role") == "user" and item.get("content", "").strip()
        ]

        if previous_user_messages:
            previous_user_message = previous_user_messages[-1]
            contextual_message = (
                f"Önceki kullanıcı sorusu: {previous_user_message}\n"
                f"Şu anki kullanıcı sorusu: {message}"
            )

    # Takip sorularında önceki analysis ve sensor_data daha faydalı olabilir
    effective_sensor_data = sensor_data
    effective_analysis = advice_result

    if is_follow_up:
        if last_sensor_data:
            effective_sensor_data = last_sensor_data
        if last_analysis:
            effective_analysis = last_analysis

    # Selamlaşmada direkt kısa cevap dön
    if is_greeting:
        answer = (
            "Merhaba, ben ChatFarm asistanıyım. "
            "İstersen mevcut durumu analiz edebilir, riskleri söyleyebilir "
            "veya neden bir öneri verildiğini açıklayabilirim."
        )

        # Session güncelle
        request.session["last_sensor_data"] = sensor_data
        request.session["last_analysis"] = advice_result
        request.session["last_answer"] = answer
        request.session["last_topic"] = last_topic or "general"
        request.session["last_rag_query"] = last_rag_query or ""

        return Response(
            {
                "message": message,
                "sensor_data": sensor_data,
                "analysis": advice_result,
                "rag": {
                    "topic": last_topic or "general",
                    "coverage_ok": True,
                    "query": last_rag_query or "",
                    "chunks": [],
                },
                "prompt": "",
                "explanations": [],
                "answer": answer,
            }
        )

    # RAG bağlamı al
    rag_result = get_rag_context(
        user_message=contextual_message,
        sensor_data=effective_sensor_data,
        analysis=effective_analysis,
        top_k=5,
    )

    retrieved_chunks = rag_result.get("chunks", [])
    explanations = [chunk.get("content", "") for chunk in retrieved_chunks]

    coverage_ok = rag_result.get("coverage_ok", False)
    topic = rag_result.get("topic", "general")
    rag_query = rag_result.get("rag_query", "")

    # Eğer coverage boşsa ama takip sorusuysa önceki topic'i korumak faydalı olabilir
    if is_follow_up and not coverage_ok and last_topic:
        topic = last_topic

    # Prompt oluştur
    prompt = build_chat_prompt(
        user_message=contextual_message,
        sensor_data=effective_sensor_data,
        analysis=effective_analysis,
        rag_chunks=retrieved_chunks,
        rag_coverage_ok=coverage_ok,
    )

    # Status / reason sorularında modelin "veri yok" deme ihtimalini azaltmak için
    if is_status or is_reason or is_follow_up:
        answer = generate_llm_answer(
            prompt,
            rag_coverage_ok=True,
        )
    else:
        answer = generate_llm_answer(
            prompt,
            rag_coverage_ok=coverage_ok,
        )

    # Session'a son başarılı bağlamı kaydet
    request.session["last_sensor_data"] = sensor_data
    request.session["last_analysis"] = advice_result
    request.session["last_answer"] = answer
    request.session["last_topic"] = topic
    request.session["last_rag_query"] = rag_query

    return Response(
        {
            "message": message,
            "sensor_data": sensor_data,
            "analysis": advice_result,
            "rag": {
                "topic": topic,
                "coverage_ok": coverage_ok,
                "query": rag_query,
                "chunks": retrieved_chunks,
            },
            "prompt": prompt,
            "explanations": explanations,
            "answer": answer,
        }
    )