from rest_framework import serializers


class TelemetryIngestSerializer(serializers.Serializer):
    device_uid = serializers.CharField(max_length=100)

    temperature = serializers.FloatField(required=False, allow_null=True)
    humidity = serializers.FloatField(required=False, allow_null=True)
    soil_moisture = serializers.FloatField(required=False, allow_null=True)
    light = serializers.FloatField(required=False, allow_null=True)
    water_temperature = serializers.FloatField(required=False, allow_null=True)
    mq135 = serializers.FloatField(required=False, allow_null=True)

    # Şimdilik kalsın istiyorsan bırakabiliriz
    ph = serializers.FloatField(required=False, allow_null=True)