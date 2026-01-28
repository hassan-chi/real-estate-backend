from ninja import Router, Query
from core.api.auth import GlobalAuth
from core.api.schemas.pagination import PaginationParams, PaginatedResponse
from core.api.schemas.property_request import (
    PropertyRequestCreateSchema,
    PropertyRequestOut,
    PropertyRequestUpdateSchema
)
from core.api.utils.messageOut import MessageOut
from core.models import PropertyRequest, Property, CustomUser
from django.core.paginator import Paginator

router = Router(tags=["property_requests"])

PaginatedPropertyRequestOut = PaginatedResponse[PropertyRequestOut]


@router.post("/", auth=GlobalAuth(), response={201: PropertyRequestOut, 404: MessageOut})
def create_property_request(request, payload: PropertyRequestCreateSchema):
    user = request.user

    try:
        property_instance = Property.objects.get(id=payload.property_id)
    except Property.DoesNotExist:
        return 404, MessageOut(title="failed", message="Property not found.")

    # Create the request
    property_request = PropertyRequest.objects.create(
        user=user,
        property=property_instance,
        request_type=payload.request_type,
        message=payload.message,
        status='new'
    )

    return 201, property_request


@router.get("/my-requests", auth=GlobalAuth(), response=PaginatedPropertyRequestOut)
def list_my_requests(request, pagination: PaginationParams = Query(...)):
    """List requests made by the current user (as a buyer/tenant)"""

    user = request.user
    queryset = PropertyRequest.objects.filter(user=user).select_related('property', 'user').order_by('-created_at')

    paginator = Paginator(queryset, pagination.page_size)
    page_obj = paginator.get_page(pagination.page)

    return {
        "items": list(page_obj),
        "count": paginator.count,
        "page": page_obj.number,
        "page_size": pagination.page_size,
        "total_pages": paginator.num_pages,
    }


@router.get("/leads", auth=GlobalAuth(), response=PaginatedPropertyRequestOut)
def list_property_leads(request, pagination: PaginationParams = Query(...)):
    """List leads (requests) for properties owned by the current user"""
    from ninja import Query

    user = request.user

    # Only show leads for properties owned by the user
    # Or if user is admin, show all
    if user.role == 'admin':
        queryset = PropertyRequest.objects.all()
    elif user.role in ['agent', 'seller']:
        queryset = PropertyRequest.objects.filter(property__owner=user)
    else:
        return []

    queryset = queryset.select_related('property', 'user').order_by('-created_at')

    paginator = Paginator(queryset, pagination.page_size)
    page_obj = paginator.get_page(pagination.page)

    return {
        "items": list(page_obj),
        "count": paginator.count,
        "page": page_obj.number,
        "page_size": pagination.page_size,
        "total_pages": paginator.num_pages,
    }


@router.patch("/{request_id}", auth=GlobalAuth(), response={200: PropertyRequestOut, 403: MessageOut, 404: MessageOut})
def update_property_request(request, request_id: int, payload: PropertyRequestUpdateSchema):
    """Update request status or assign agent (for property owners/agents)"""
    user = request.user

    try:
        property_request = PropertyRequest.objects.select_related('property').get(id=request_id)
    except PropertyRequest.DoesNotExist:
        return 404, MessageOut(title="failed", message="Request not found.")

    # Check authorization - only property owner, assigned agent, or admin can update
    # The assigned agent logic depends on if agents are assigned to properties or requests
    is_owner = property_request.property.owner == user
    is_assigned = property_request.assigned_agent == user
    is_admin = user.role == 'admin'

    if not (is_owner or is_assigned or is_admin):
        return 403, MessageOut(title="failed", message="You are not authorized to update this request.")

    if payload.status:
        property_request.status = payload.status

    if payload.assigned_agent_id and (is_owner or is_admin):
        try:
            agent = CustomUser.objects.get(id=payload.assigned_agent_id, role__in=['agent', 'admin'])
            property_request.assigned_agent = agent
        except CustomUser.DoesNotExist:
            return 400, MessageOut(title="failed", message="Invalid agent ID.")

    property_request.save()

    return property_request
