from ninja import Router
from typing import List, Optional

from django.utils import timezone

from core.api.schemas.advertisement import AdvertisementOut, AdPosition
from core.models import Advertisement

router = Router(tags=["advertisements"])


@router.get("/", response=List[AdvertisementOut])
def get_advertisements(request, position: Optional[AdPosition] = None):
    """
    Get active advertisements.
    Optionally filter by position (home, search, details).
    """
    now = timezone.now()
    
    queryset = Advertisement.objects.filter(
        active=True,
        start_date__lte=now,
        end_date__gte=now
    )
    
    if position:
        queryset = queryset.filter(position=position)
    
    return queryset.order_by('-created_at')


@router.get("/{position}", response=List[AdvertisementOut])
def get_advertisements_by_position(request, position: AdPosition):
    """Get active advertisements for a specific position."""
    now = timezone.now()
    
    return Advertisement.objects.filter(
        active=True,
        position=position,
        start_date__lte=now,
        end_date__gte=now
    ).order_by('-created_at')
