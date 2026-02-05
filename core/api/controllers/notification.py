from ninja import Router, Query
from django.utils import timezone
from django.core.paginator import Paginator

from core.api.auth import GlobalAuth
from core.api.utils.messageOut import MessageOut
from core.api.schemas.notification import (
    PaginatedNotificationOut,
)
from core.api.schemas.pagination import PaginationParams
from core.models import Notification, CustomUser

router = Router(tags=["notifications"])


@router.get("/", auth=GlobalAuth(), response=PaginatedNotificationOut)
def get_notifications(request, pagination: PaginationParams = Query(...), unread_only: bool = False):
    """Get paginated notifications for the authenticated user."""
    user: CustomUser = request.user
    
    queryset = Notification.objects.filter(user=user).order_by('-created_at')
    
    if unread_only:
        queryset = queryset.filter(is_read=False)
    
    # Get unread count before pagination
    unread_count = Notification.objects.filter(user=user, is_read=False).count()
    
    paginator = Paginator(queryset, pagination.page_size)
    page_obj = paginator.get_page(pagination.page)
    
    return {
        "items": list(page_obj),
        "count": paginator.count,
        "page": page_obj.number,
        "page_size": pagination.page_size,
        "total_pages": paginator.num_pages,
        "unread_count": unread_count,
    }



@router.post("/mark-read/{notification_id}", auth=GlobalAuth(), response={200: MessageOut, 400: MessageOut})
def mark_notifications_as_read(request, notification_id: int):
    """Mark specific notifications as read."""
    user: CustomUser = request.user
    
    notification = Notification.objects.filter(
        user=user,
        id=notification_id,
        is_read=False
    ).first()
    
    if not notification :
        return 400, MessageOut(title="info", message="No unread notifications found with the provided IDs.")
    
    notification.is_read = True
    notification.read_at = timezone.now()
    notification.save()
    
    return 200, MessageOut(title="success", message="The notification has been marked as read.")


@router.post("/mark-all-read", auth=GlobalAuth(), response=MessageOut)
def mark_all_notifications_as_read(request):
    """Mark all notifications as read for the authenticated user."""
    user: CustomUser = request.user
    
    count = Notification.objects.filter(user=user, is_read=False).update(
        is_read=True,
        read_at=timezone.now()
    )
    
    return MessageOut(title="success", message=f"Marked {count} notification(s) as read.")