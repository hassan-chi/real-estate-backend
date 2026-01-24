from ninja import Router

from core.api.auth import GlobalAuth
from core.api.controllers.auth import router as auth_router
from core.api.controllers.essentials import router as essentials_router
from core.api.controllers.property import router as property_router
from core.api.controllers.amenity import router as amenity_router

router = Router()

router.add_router("/auth", auth_router)
router.add_router('/essentials', essentials_router)
router.add_router('/property', property_router)
router.add_router('/amenities', amenity_router)

@router.get("/health")
def mobile_health_check(request):
    return {"message": "API is healthy!", "type": "api"}


@router.get("/status")
def mobile_status(request):
    return {"status": "ok", "api": "api"}
