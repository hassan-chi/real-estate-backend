from typing import List
from ninja import Router, Query
from ninja.pagination import paginate
from core.models import Property
from core.api.schemas.property import PropertyOut, PropertyFilterSchema

router = Router(tags=["property"])


@router.get("/", response=List[PropertyOut])
@paginate
def get_properties(request, filters: PropertyFilterSchema = Query(...)):
    queryset = Property.objects.filter(approved=True , status="available").select_related('currency', 'province', 'city').prefetch_related('images', 'amenities')

    if filters.province_id:
        queryset = queryset.filter(province_id=filters.province_id)

    if filters.city_id:
        queryset = queryset.filter(city_id=filters.city_id)

    if filters.listing_type:
        queryset = queryset.filter(listing_type=filters.listing_type)

    if filters.min_price:
        queryset = queryset.filter(price__gte=filters.min_price)

    if filters.max_price:
        queryset = queryset.filter(price__lte=filters.max_price)

    if filters.bedrooms:
        queryset = queryset.filter(bedrooms__gte=filters.bedrooms)

    if filters.amenities:
        queryset = queryset.filter(amenities__id__in=filters.amenities)

    return queryset
