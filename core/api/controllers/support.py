from ninja import Router
from typing import List

from core.api.schemas.support import SupportOut
from core.models import Support

router = Router(tags=["support"])


@router.get("/", response=List[SupportOut])
def get_support_items(request):
    """Get all support items."""
    return Support.objects.all().order_by('-created_at')
