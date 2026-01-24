from ninja import Router, Query, File, Form
from ninja.pagination import paginate
from typing import List
from ninja.files import UploadedFile
from cities_light.models import City, Region
from django.shortcuts import get_object_or_404
from core.api.auth import GlobalAuth
from core.api.utils.messageOut import MessageOut
from core.models import Property, Currency, Amenity, PropertyImage, CustomUser
from core.api.schemas.property import PropertyOut, PropertyFilterSchema, PropertyCreateSchema
from django.contrib.gis.geos import Point

router = Router(tags=["property"])


@router.post("/", auth=GlobalAuth(), response={200: PropertyOut, 403: MessageOut})
def create_property(request, payload: Form[PropertyCreateSchema], images: List[UploadedFile] = File(...)):
    user: CustomUser = request.auth['user']
    if not user.profile_completed:
        return 403, MessageOut(title="fail", message="Please complete your profile first.")
    if user.role not in ['agent', 'admin', 'seller']:
        return 403, MessageOut(title="fail", message="You are not authorized to create a property.")

    # Validate foreign keys
    try:
        province = Region.objects.get(id=payload.province_id)
    except Region.DoesNotExist:
        return 400, MessageOut(title="failed", message="Province not found.")

    try:
        city = City.objects.get(id=payload.city_id)
    except City.DoesNotExist:
        return 400, MessageOut(title="failed", message="City not found.")

    if city.region_id != province.id:
        return 400, MessageOut(title="failed", message="City does not belong to province.")

    try:
        Currency.objects.get(id=payload.currency_id)
    except Currency.DoesNotExist:
        return 400, MessageOut(title="failed", message="Currency not found.")

    amenity_ids = [int(x) for x in (payload.amenity_ids or "").split(",") if x.strip()]
    amenities = Amenity.objects.filter(id__in=amenity_ids)

    # optional strict validation (so missing IDs return 400)
    if len(amenities) != len(set(amenity_ids)):
        found = set(amenities.values_list("id", flat=True))
        missing = [i for i in amenity_ids if i not in found]
        return 400, MessageOut(title="failed", message=f"Amenities not found: {missing}")

    property_data = payload.dict()
    property_data.pop('amenity_ids', None)
    property_data.pop('longitude', None)
    property_data.pop('latitude', None)

    location = None
    if payload.longitude is not None and payload.latitude is not None:
        location = Point(payload.longitude, payload.latitude, srid=4326)

    new_property = Property.objects.create(owner=user, location=location, **property_data)
    new_property.amenities.set(amenities)

    for i, image in enumerate(images):
        PropertyImage.objects.create(
            property=new_property,
            image=image,
            order=i,
            is_cover=(i == 0)
        )

    return Property.objects.select_related('currency', 'province', 'city').prefetch_related('images', 'amenities').get(
        id=new_property.id)


@router.get("/", response=List[PropertyOut])
@paginate
def get_properties(request, filters: PropertyFilterSchema = Query(...)):
    queryset = Property.objects.filter(approved=True, status="available").select_related('currency', 'province',
                                                                                         'city').prefetch_related(
        'images', 'amenities')

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
        queryset = queryset.filter(amenities__id__in=filters.amenities).distinct()

    return queryset


@router.get("/{property_id}", response=PropertyOut)
def get_property_details(request, property_id: int):
    return Property.objects.select_related('currency', 'province', 'city').prefetch_related('images', 'amenities').get(
        id=property_id, approved=True)
