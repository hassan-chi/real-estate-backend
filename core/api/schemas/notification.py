from datetime import datetime
from enum import Enum
from typing import Optional, List

from ninja import Schema, Field


class NotificationType(str, Enum):
    PROPERTY_SOLD = 'property_sold'
    PROPERTY_RENTED = 'property_rented'
    PROPERTY_APPROVED = 'property_approved'
    PROPERTY_REJECTED = 'property_rejected'
    NEW_REQUEST = 'new_request'
    REQUEST_STATUS_CHANGED = 'request_status'
    REQUEST_ASSIGNED = 'request_assigned'
    SUBSCRIPTION_EXPIRING = 'sub_expiring'
    SUBSCRIPTION_EXPIRED = 'sub_expired'
    SYSTEM = 'system'
    PROMO = 'promo'


class NotificationOut(Schema):
    id: int
    notification_type: NotificationType
    title: str
    message: str
    related_property_id: Optional[int] = None
    related_request_id: Optional[int] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime


class PaginatedNotificationOut(Schema):
    items: List[NotificationOut]
    count: int = Field(..., description="Total number of notifications")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
    unread_count: int = Field(..., description="Total unread notifications")



