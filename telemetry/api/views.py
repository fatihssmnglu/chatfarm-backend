from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from devices.models import Device
from telemetry.models import Measurement
from telemetry.api.serializers import TelemetryIngestSerializer


class TelemetryAPIView(APIView):
    def post(self, request):
        serializer = TelemetryIngestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        device_uid = validated_data["device_uid"]

        try:
            device = Device.objects.get(device_uid=device_uid)
        except Device.DoesNotExist:
            return Response(
                {"error": "Device not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        device.last_seen = timezone.now()
        device.save()

        measurement = Measurement.objects.create(
            device=device,
            temperature=validated_data.get("temperature"),
            humidity=validated_data.get("humidity"),
            soil_moisture=validated_data.get("soil_moisture"),
            light=validated_data.get("light"),
            water_temperature=validated_data.get("water_temperature"),
            mq135=validated_data.get("mq135"),
            ph=validated_data.get("ph"),
        )

        return Response(
            {
                "status": "ok",
                "message": "Telemetry received successfully.",
                "measurement_id": measurement.id,
            },
            status=status.HTTP_201_CREATED
        )