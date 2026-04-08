from django.shortcuts import render
from telemetry.models import Measurement, Alert, IrrigationRecommendation
from devices.models import Device
from django.utils import timezone
from datetime import timedelta


def dashboard(request):
    latest_measurement = Measurement.objects.order_by("-created_at").first()
    last_10_measurements = Measurement.objects.order_by("-created_at")[:10]

    latest_alert = Alert.objects.order_by("-created_at").first()
    latest_recommendation = IrrigationRecommendation.objects.order_by("-created_at").first()

    chart_measurements = list(Measurement.objects.order_by("-created_at")[:10])
    chart_measurements.reverse()

    chart_labels = [
        measurement.created_at.strftime("%H:%M:%S")
        for measurement in chart_measurements
    ]

    soil_chart_data = [
        measurement.soil_moisture if measurement.soil_moisture is not None else 0
        for measurement in chart_measurements
    ]

    light_chart_data = [
        measurement.light if measurement.light is not None else 0
        for measurement in chart_measurements
    ]

    temperature_chart_data = [
        measurement.temperature if measurement.temperature is not None else 0
        for measurement in chart_measurements
    ]

    humidity_chart_data = [
        measurement.humidity if measurement.humidity is not None else 0
        for measurement in chart_measurements
    ]

    water_temp_chart_data = [
        measurement.water_temperature if measurement.water_temperature is not None else 0
        for measurement in chart_measurements
    ]

    mq135_chart_data = [
        measurement.mq135 if measurement.mq135 is not None else 0
        for measurement in chart_measurements
    ]

    # TOPRAK NEM DURUMU
    moisture_status = "Bilinmiyor"
    moisture_color = "#6c757d"

    if latest_measurement and latest_measurement.soil_moisture is not None:
        value = latest_measurement.soil_moisture

        if value <= 20:
            moisture_status = "Kritik Kuru"
            moisture_color = "#dc3545"
        elif value < 30:
            moisture_status = "Kuru"
            moisture_color = "#f59f00"
        else:
            moisture_status = "İyi"
            moisture_color = "#198754"

    # IŞIK DURUMU
    light_status = "Bilinmiyor"
    light_color = "#6c757d"

    if latest_measurement and latest_measurement.light is not None:
        light_value = latest_measurement.light

        if light_value < 1500:
            light_status = "Parlak"
            light_color = "#f59f00"
        elif 1500 <= light_value <= 3000:
            light_status = "Orta"
            light_color = "#198754"
        else:
            light_status = "Karanlık"
            light_color = "#343a40"

    # CİHAZ DURUMU
    latest_device = Device.objects.order_by("-created_at").first()
    device_status = "Offline"
    device_color = "#dc3545"

    if latest_device and latest_device.last_seen:
        if latest_device.last_seen >= timezone.now() - timedelta(seconds=10):
            device_status = "Online"
            device_color = "#198754"

    context = {
        "latest_measurement": latest_measurement,
        "last_10_measurements": last_10_measurements,

        "chart_labels": chart_labels,
        "soil_chart_data": soil_chart_data,
        "light_chart_data": light_chart_data,
        "temperature_chart_data": temperature_chart_data,
        "humidity_chart_data": humidity_chart_data,
        "water_temp_chart_data": water_temp_chart_data,
        "mq135_chart_data": mq135_chart_data,

        "moisture_status": moisture_status,
        "moisture_color": moisture_color,

        "light_status": light_status,
        "light_color": light_color,

        "device_status": device_status,
        "device_color": device_color,

        "latest_alert": latest_alert,
        "latest_recommendation": latest_recommendation,
    }

    return render(request, "telemetry/dashboard.html", context)