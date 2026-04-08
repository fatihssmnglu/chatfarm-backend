from django.contrib import admin
from .models import Measurement,Alert,IrrigationRecommendation

admin.site.register(Measurement)
admin.site.register(Alert)
admin.site.register(IrrigationRecommendation)