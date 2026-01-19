from ninja import Router

router = Router()

@router.get("/health")
def mobile_health_check(request):
    return {"message": "API is healthy!", "type": "api"}

@router.get("/status")
def mobile_status(request):
    return {"status": "ok", "api": "api"}
