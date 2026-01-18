from django.urls import path
from ninja import NinjaAPI
from .dashboard.api import router as dashboard_router
from .mobile.api import router as mobile_router

# Separate API instances for dashboard and mobile with unique namespaces
dashboard_api = NinjaAPI(
    title="Dashboard API", 
    version="1.0.0",
    description="API endpoints for dashboard functionality",
    urls_namespace="dashboard"
)
dashboard_api.add_router("", dashboard_router, tags=["Dashboard"])

mobile_api = NinjaAPI(
    title="Mobile API", 
    version="1.0.0",
    description="API endpoints for mobile applications",
    urls_namespace="mobile"
)
mobile_api.add_router("", mobile_router, tags=["Mobile"])

urlpatterns = [
    path("api/dashboard/", dashboard_api.urls),
    path("api/mobile/", mobile_api.urls),
]
