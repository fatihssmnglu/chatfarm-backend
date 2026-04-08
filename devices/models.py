from django.db import models
from farms.models import Farm


class Device(models.Model):

    name = models.CharField(max_length=100)

    device_uid = models.CharField(max_length=100, unique=True)

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE)

    last_seen = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name