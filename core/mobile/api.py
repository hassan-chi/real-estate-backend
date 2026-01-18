from ninja import Router

router = Router()

@router.get("/health")
def mobile_health_check(request):
    return {"message": "Mobile API is healthy!", "type": "mobile"}

@router.get("/status")
def mobile_status(request):
    return {"status": "ok", "api": "mobile"}
