from ninja import Router

from core.api.auth import GlobalAuth
from core.api.controllers.auth import router as auth_router
from core.api.controllers.essentials import router as essentials_router
from core.api.controllers.property import router as property_router
from core.api.controllers.amenity import router as amenity_router
from core.api.controllers.property_request import router as property_requests_router
from core.api.controllers.notification import router as notification_router
from core.api.controllers.advertisement import router as advertisement_router
from core.api.controllers.support import router as support_router

router = Router()

router.add_router("/auth", auth_router)
router.add_router('/essentials', essentials_router)
router.add_router('/property', property_router)
router.add_router('/amenities', amenity_router)
router.add_router('/leads', property_requests_router)
router.add_router('/notifications', notification_router)
router.add_router('/ads', advertisement_router)
router.add_router('/support', support_router)

@router.get("/health")
def mobile_health_check(request):
    return {"message": "API is healthy!", "type": "api"}


@router.get("/status")
def mobile_status(request):
    return {"status": "ok", "api": "api"}
