from django.db import models
from devices.models import Device


class Measurement(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)

    temperature = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)

    soil_moisture = models.FloatField(null=True, blank=True)

    ph = models.FloatField(null=True, blank=True)
    light = models.FloatField(null=True, blank=True)

    water_temperature = models.FloatField(null=True, blank=True)
    mq135 = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)




class Alert(models.Model):
    measurement = models.ForeignKey(Measurement, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=100)
    severity = models.CharField(max_length=50)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.alert_type} - {self.severity}"    
    

class IrrigationRecommendation(models.Model):
    measurement = models.ForeignKey(Measurement, on_delete=models.CASCADE)
    score = models.IntegerField()
    recommendation = models.CharField(max_length=100)
    water_amount_mm = models.FloatField(null=True, blank=True)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recommendation} - {self.score}"