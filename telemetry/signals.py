from django.db.models.signals import post_save
from django.dispatch import receiver

from telemetry.models import Measurement
from telemetry.services.rule_engine import (
    create_alert_for_measurement,
    create_recommendation_for_measurement,
)


@receiver(post_save, sender=Measurement)
def measurement_post_save(sender, instance, created, **kwargs):
    if created:
        create_alert_for_measurement(instance)
        create_recommendation_for_measurement(instance)