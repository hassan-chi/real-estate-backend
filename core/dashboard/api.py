from ninja import Router

router = Router()


@router.get("/health")
def dashboard_health_check(request):
    return {"message": "Dashboard API is healthy!", "type": "dashboard"}
