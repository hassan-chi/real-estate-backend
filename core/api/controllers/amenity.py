from typing import List
from ninja import Router
from core.models import Amenity
from core.api.schemas.property import AmenityOut

router = Router(tags=["amenities"])


@router.get("/", response=List[AmenityOut])
def get_amenities(request):
    return Amenity.objects.all()
