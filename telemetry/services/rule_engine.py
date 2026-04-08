from telemetry.models import Alert, IrrigationRecommendation


def calculate_irrigation(measurement):
    score = 0
    reasons = []

    if measurement.soil_moisture is not None:
        if measurement.soil_moisture <= 20:
            score += 40
            reasons.append("Toprak nemi kritik düzeyde düşük")
        elif measurement.soil_moisture < 30:
            score += 30
            reasons.append("Toprak nemi düşük")

    if measurement.temperature is not None:
        if measurement.temperature >= 35:
            score += 25
            reasons.append("Sıcaklık çok yüksek")
        elif measurement.temperature > 30:
            score += 20
            reasons.append("Sıcaklık yüksek")

    if measurement.humidity is not None:
        if measurement.humidity <= 30:
            score += 15
            reasons.append("Hava nemi çok düşük")
        elif measurement.humidity < 40:
            score += 10
            reasons.append("Hava nemi düşük")

    if score >= 60:
        decision = "Acil sulama önerilir"
        severity = "critical"
        water_amount_mm = 40
    elif score >= 40:
        decision = "Sulama önerilir"
        severity = "warning"
        water_amount_mm = 25
    else:
        decision = "Sulama gerekmez"
        severity = "info"
        water_amount_mm = 0

    return {
        "score": score,
        "decision": decision,
        "reasons": reasons,
        "severity": severity,
        "water_amount_mm": water_amount_mm,
    }


def create_alert_for_measurement(measurement):
    result = calculate_irrigation(measurement)

    if result["score"] < 40:
        return None

    message = f"{result['decision']} | Nedenler: {', '.join(result['reasons'])}"

    alert = Alert.objects.create(
        measurement=measurement,
        alert_type="irrigation",
        severity=result["severity"],
        message=message,
    )

    return alert


def create_recommendation_for_measurement(measurement):
    result = calculate_irrigation(measurement)

    reason_text = ", ".join(result["reasons"]) if result["reasons"] else "Sulama gerektiren kritik durum yok"

    recommendation = IrrigationRecommendation.objects.create(
        measurement=measurement,
        score=result["score"],
        recommendation=result["decision"],
        water_amount_mm=result["water_amount_mm"],
        reason=reason_text,
    )

    return recommendation

def create_alert_for_measurement(measurement):
    # Zaten alert var mı kontrol et
    existing = Alert.objects.filter(measurement=measurement, alert_type="irrigation").first()
    if existing:
        return existing

    result = calculate_irrigation(measurement)

    if result["score"] < 40:
        return None

    message = f"{result['decision']} | Nedenler: {', '.join(result['reasons'])}"

    alert = Alert.objects.create(
        measurement=measurement,
        alert_type="irrigation",
        severity=result["severity"],
        message=message,
    )

    return alert

def create_recommendation_for_measurement(measurement):
    existing = IrrigationRecommendation.objects.filter(measurement=measurement).first()
    if existing:
        return existing

    result = calculate_irrigation(measurement)

    reason_text = ", ".join(result["reasons"]) if result["reasons"] else "Sulama gerektiren kritik durum yok"

    recommendation = IrrigationRecommendation.objects.create(
        measurement=measurement,
        score=result["score"],
        recommendation=result["decision"],
        water_amount_mm=result["water_amount_mm"],
        reason=reason_text,
    )

    return recommendation