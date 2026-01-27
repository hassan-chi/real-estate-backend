from ninja import Router, Query, File, Form
from typing import List
from ninja.files import UploadedFile
from cities_light.models import City, Region
from core.api.auth import GlobalAuth
from core.api.utils.messageOut import MessageOut
from core.models import Property, Currency, Amenity, PropertyImage, CustomUser
from core.api.schemas.property import PropertyOut, PropertyFilterSchema, PropertyCreateSchema, PropertyUpdateSchema, \
    PropertyAmenityUpdateSchema, PaginatedPropertyOut, ImageReorderSchema
from core.api.schemas.pagination import PaginationParams
from django.contrib.gis.geos import Point
from django.db import models
from django.db import transaction
from django.core.paginator import Paginator

router = Router(tags=["property"])


@router.post("/", auth=GlobalAuth(), response={200: PropertyOut, 403: MessageOut})
def create_property(request, payload: Form[PropertyCreateSchema], images: List[UploadedFile] = File(...)):
    user: CustomUser = request.user
    if not user.profile_completed:
        return 403, MessageOut(title="fail", message="Please complete your profile first.")
    if user.role not in ['agent', 'admin', 'seller']:
        return 403, MessageOut(title="fail", message="You are not authorized to create a property.")

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


@router.put("/{property_id}", auth=GlobalAuth(), response={200: PropertyOut, 403: MessageOut, 404: MessageOut})
def update_property(request, property_id: int, payload: PropertyUpdateSchema):
    user: CustomUser = request.user
    if not user.profile_completed:
        return 403, MessageOut(title="fail", message="Please complete your profile first.")
    if user.role not in ['agent', 'admin', 'seller']:
        return 403, MessageOut(title="fail", message="You are not authorized to update a property.")

    try:
        property_instance = Property.objects.get(id=property_id)
    except Property.DoesNotExist:
        return 404, MessageOut(title="failed", message="Property not found.")

    if property_instance.owner != user and user.role != 'admin':
        return 403, MessageOut(title="fail", message="You are not authorized to update this property.")

    for attr, value in payload.dict(exclude_unset=True).items():
        setattr(property_instance, attr, value)

    property_instance.save()

    return property_instance


@router.post("/{property_id}/amenities", auth=GlobalAuth(), response={200: PropertyOut, 403: MessageOut, 404: MessageOut})
def update_property_amenities(request, property_id: int, payload: PropertyAmenityUpdateSchema):
    user: CustomUser = request.user
    if not user.profile_completed:
        return 403, MessageOut(title="fail", message="Please complete your profile first.")
    if user.role not in ['agent', 'admin', 'seller']:
        return 403, MessageOut(title="fail", message="You are not authorized to update a property.")

    try:
        property_instance = Property.objects.get(id=property_id)
    except Property.DoesNotExist:
        return 404, MessageOut(title="failed", message="Property not found.")

    if property_instance.owner != user and user.role != 'admin':
        return 403, MessageOut(title="fail", message="You are not authorized to update this property.")

    amenities = Amenity.objects.filter(id__in=payload.amenity_ids)
    if len(amenities) != len(payload.amenity_ids):
        return 400, MessageOut(title="failed", message="One or more amenities not found.")
    
    property_instance.amenities.set(amenities)
    
    return property_instance


@router.delete("/{property_id}/amenities/{amenity_id}", auth=GlobalAuth(), response={200: MessageOut, 403: MessageOut, 404: MessageOut})
def delete_property_amenity(request, property_id: int, amenity_id: int):
    user: CustomUser = request.user
    if not user.profile_completed:
        return 403, MessageOut(title="fail", message="Please complete your profile first.")
    if user.role not in ['agent', 'admin', 'seller']:
        return 403, MessageOut(title="fail", message="You are not authorized to update a property.")

    try:
        property_instance = Property.objects.get(id=property_id)
    except Property.DoesNotExist:
        return 404, MessageOut(title="failed", message="Property not found.")

    if property_instance.owner != user and user.role != 'admin':
        return 403, MessageOut(title="fail", message="You are not authorized to update this property.")

    try:
        amenity = Amenity.objects.get(id=amenity_id)
    except Amenity.DoesNotExist:
        return 404, MessageOut(title="failed", message="Amenity not found.")

    property_instance.amenities.remove(amenity)

    return 200, MessageOut(title="success", message="Amenity removed from property.")


@router.post("/{property_id}/images", auth=GlobalAuth(), response={200: PropertyOut, 403: MessageOut, 404: MessageOut})
def add_property_images(request, property_id: int, images: List[UploadedFile] = File(...)):
    user: CustomUser = request.user
    if not user.profile_completed:
        return 403, MessageOut(title="fail", message="Please complete your profile first.")
    if user.role not in ['agent', 'admin', 'seller']:
        return 403, MessageOut(title="fail", message="You are not authorized to update a property.")

    try:
        property_instance = Property.objects.get(id=property_id)
    except Property.DoesNotExist:
        return 404, MessageOut(title="failed", message="Property not found.")

    if property_instance.owner != user and user.role != 'admin':
        return 403, MessageOut(title="fail", message="You are not authorized to update this property.")

    # Get the current max order to append new images
    existing_images = PropertyImage.objects.filter(property=property_instance)
    max_order = existing_images.aggregate(models.Max('order'))['order__max'] or -1

    # Add new images
    for i, image in enumerate(images):
        PropertyImage.objects.create(
            property=property_instance,
            image=image,
            order=max_order + i + 1,
            is_cover=False
        )

    return Property.objects.select_related('currency', 'province', 'city').prefetch_related('images', 'amenities').get(
        id=property_instance.id)


@router.patch("/{property_id}/images/{image_id}/set-cover", auth=GlobalAuth(), response={200: PropertyOut, 403: MessageOut, 404: MessageOut})
def set_cover_image(request, property_id: int, image_id: int):
    user: CustomUser = request.user
    if not user.profile_completed:
        return 403, MessageOut(title="fail", message="Please complete your profile first.")
    if user.role not in ['agent', 'admin', 'seller']:
        return 403, MessageOut(title="fail", message="You are not authorized to update a property.")

    try:
        property_instance = Property.objects.get(id=property_id)
    except Property.DoesNotExist:
        return 404, MessageOut(title="failed", message="Property not found.")

    if property_instance.owner != user and user.role != 'admin':
        return 403, MessageOut(title="fail", message="You are not authorized to update this property.")

    try:
        new_cover_image = PropertyImage.objects.get(id=image_id, property=property_instance)
    except PropertyImage.DoesNotExist:
        return 404, MessageOut(title="failed", message="Image not found for this property.")

    # Unset the current cover image
    PropertyImage.objects.filter(property=property_instance, is_cover=True).update(is_cover=False)

    # Set the new cover image
    new_cover_image.is_cover = True
    new_cover_image.save()

    return Property.objects.select_related('currency', 'province', 'city').prefetch_related('images', 'amenities').get(
        id=property_instance.id)


@router.patch("/{property_id}/images/reorder", auth=GlobalAuth(), response={200: PropertyOut, 400: MessageOut, 403: MessageOut, 404: MessageOut})
def reorder_property_images(request, property_id: int, payload: ImageReorderSchema):
    user: CustomUser = request.user
    if not user.profile_completed:
        return 403, MessageOut(title="fail", message="Please complete your profile first.")
    if user.role not in ['agent', 'admin', 'seller']:
        return 403, MessageOut(title="fail", message="You are not authorized to update a property.")

    try:
        property_instance = Property.objects.get(id=property_id)
    except Property.DoesNotExist:
        return 404, MessageOut(title="failed", message="Property not found.")

    if property_instance.owner != user and user.role != 'admin':
        return 403, MessageOut(title="fail", message="You are not authorized to update this property.")

    # Get the image to move
    try:
        image_to_move = PropertyImage.objects.get(id=payload.image_id, property=property_instance)
    except PropertyImage.DoesNotExist:
        return 404, MessageOut(title="failed", message="Image not found for this property.")

    # Get all images for this property ordered by current order
    all_images = list(PropertyImage.objects.filter(property=property_instance).order_by('order'))
    
    # Validate new position
    if payload.new_position < 0 or payload.new_position >= len(all_images):
        return 400, MessageOut(title="failed", message=f"Invalid position. Must be between 0 and {len(all_images) - 1}.")

    # Get current position
    current_position = next(i for i, img in enumerate(all_images) if img.id == image_to_move.id)
    
    # If position hasn't changed, no need to update
    if current_position == payload.new_position:
        return Property.objects.select_related('currency', 'province', 'city').prefetch_related('images', 'amenities').get(
            id=property_instance.id)

    # Remove image from current position and insert at new position
    all_images.pop(current_position)
    all_images.insert(payload.new_position, image_to_move)

    # Update all orders
    from django.db import transaction
    
    with transaction.atomic():
        for index, image in enumerate(all_images):
            image.order = index
            image.save()

    return Property.objects.select_related('currency', 'province', 'city').prefetch_related('images', 'amenities').get(
        id=property_instance.id)


@router.delete("/{property_id}/images/{image_id}", auth=GlobalAuth(), response={200: MessageOut, 403: MessageOut, 404: MessageOut})
def delete_property_image(request, property_id: int, image_id: int):
    user: CustomUser = request.user
    if not user.profile_completed:
        return 403, MessageOut(title="fail", message="Please complete your profile first.")
    if user.role not in ['agent', 'admin', 'seller']:
        return 403, MessageOut(title="fail", message="You are not authorized to update a property.")

    try:
        property_instance = Property.objects.get(id=property_id)
    except Property.DoesNotExist:
        return 404, MessageOut(title="failed", message="Property not found.")

    if property_instance.owner != user and user.role != 'admin':
        return 403, MessageOut(title="fail", message="You are not authorized to update this property.")

    try:
        image_to_delete = PropertyImage.objects.get(id=image_id, property=property_instance)
    except PropertyImage.DoesNotExist:
        return 404, MessageOut(title="failed", message="Image not found for this property.")

    # Check if this is the cover image
    was_cover = image_to_delete.is_cover

    # Delete the physical file from storage
    if image_to_delete.image:
        image_to_delete.image.delete(save=False)

    # Delete the database record
    image_to_delete.delete()

    # If the deleted image was the cover, set the first remaining image as cover
    if was_cover:
        first_image = PropertyImage.objects.filter(property=property_instance).order_by('order').first()
        if first_image:
            first_image.is_cover = True
            first_image.save()

    return 200, MessageOut(title="success", message="Image deleted successfully.")








@router.get("/myproperty", auth=GlobalAuth(), response=PaginatedPropertyOut)
def get_my_properties(request, pagination: PaginationParams = Query(...)):
    """Get all properties owned by the authenticated user."""
    
    user: CustomUser = request.user
    queryset = Property.objects.filter(owner=user).select_related(
        'currency', 'province', 'city'
    ).prefetch_related('images', 'amenities').order_by('-id')

    paginator = Paginator(queryset, pagination.page_size)
    page_obj = paginator.get_page(pagination.page)
    
    return {
        "items": list(page_obj),
        "count": paginator.count,
        "page": page_obj.number,
        "page_size": pagination.page_size,
        "total_pages": paginator.num_pages,
    }


@router.get("/", response=PaginatedPropertyOut)
def get_properties(request, filters: PropertyFilterSchema = Query(...), pagination: PaginationParams = Query(...)):
    
    queryset = Property.objects.filter(approved=True, status="available").select_related('currency', 'province',
                                                                                         'city').prefetch_related(
        'images', 'amenities')

    if filters.search:
        queryset = queryset.filter(
            models.Q(title__icontains=filters.search) | 
            models.Q(description__icontains=filters.search)
        )

    if filters.property_type:
        queryset = queryset.filter(property_type=filters.property_type)

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

    paginator = Paginator(queryset, pagination.page_size)
    page_obj = paginator.get_page(pagination.page)
    
    return {
        "items": list(page_obj),
        "count": paginator.count,
        "page": page_obj.number,
        "page_size": pagination.page_size,
        "total_pages": paginator.num_pages,
    }


@router.get("/{property_id}", response=PropertyOut)
def get_property_details(request, property_id: int):
    return Property.objects.select_related('currency', 'province', 'city').prefetch_related('images', 'amenities').get(
        id=property_id, approved=True)


@router.delete("/{property_id}", auth=GlobalAuth(), response={200: MessageOut, 403: MessageOut, 404: MessageOut})
def delete_property(request, property_id: int):
    user: CustomUser = request.user
    if not user.profile_completed:
        return 403, MessageOut(title="fail", message="Please complete your profile first.")
    if user.role not in ['agent', 'admin', 'seller']:
        return 403, MessageOut(title="fail", message="You are not authorized to delete a property.")

    try:
        property_instance = Property.objects.get(id=property_id)
    except Property.DoesNotExist:
        return 404, MessageOut(title="failed", message="Property not found.")

    if property_instance.owner != user and user.role != 'admin':
        return 403, MessageOut(title="fail", message="You are not authorized to delete this property.")

    property_instance.delete()

    return 200, MessageOut(title="success", message="Property deleted successfully.")

