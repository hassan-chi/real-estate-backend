from ninja import NinjaAPI
from core.dashboard.api import router as dashboard_router

api = NinjaAPI()

api.add_router("/dashboard/", dashboard_router)

@api.get("/hello")
def hello(request):
    return "Hello, world!"

@api.get("/mobile/health")
def mobile_health_check(request):
    return {"message": "Mobile API is healthy!"}
