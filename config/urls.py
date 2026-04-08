from django.contrib import admin
from django.urls import path
from telemetry.views import dashboard

from telemetry.api.views import TelemetryAPIView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/telemetry", TelemetryAPIView.as_view()),
    path("dashboard/", dashboard),
]