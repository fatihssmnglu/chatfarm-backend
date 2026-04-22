from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import include, path
from telemetry.views import dashboard
from telemetry.api.views import TelemetryAPIView


def favicon(_request):
    # Avoid noisy 404s for browsers hitting /favicon.ico during development.
    return HttpResponse(status=204)


def root(request):
    # Default landing page -> dashboard.
    return redirect("dashboard/")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/telemetry", TelemetryAPIView.as_view()),
    path("api/telemetry/", TelemetryAPIView.as_view()),
    path("favicon.ico", favicon),
    path("", root),
    path("dashboard/", dashboard),
    path("api/", include("knowledge.urls")),
]
