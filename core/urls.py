from django.urls import path
from django.http import HttpResponse
from ninja import NinjaAPI
from .api.api import router

def health(request):
    return HttpResponse("OK")

mobile_api = NinjaAPI(
    title="API",
    version="0.1.0",
    description="API endpoints",
    urls_namespace="api"
)
mobile_api.add_router("", router, tags=["Api"])

urlpatterns = [
    path("api/", mobile_api.urls),
    path("health/", health),
    path("", health),  # Also efficient for default health checks
]
