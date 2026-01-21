from ninja import Router
from core.api.controllers.auth import router as auth_router

router = Router()

router.add_router("/auth", auth_router)


@router.get("/health")
def mobile_health_check(request):
    return {"message": "API is healthy!", "type": "api"}


@router.get("/status")
def mobile_status(request):
    return {"status": "ok", "api": "api"}
