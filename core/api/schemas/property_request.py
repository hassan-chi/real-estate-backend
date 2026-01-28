from datetime import datetime
from enum import Enum
from typing import Optional

from ninja import Schema
from core.models import PropertyRequest


class RequestType(str, Enum):
    PURCHASE = 'purchase'
    RENT = 'rent'
    CALL = 'call'
    DETAILS = 'details'


class RequestStatus(str, Enum):
    NEW = 'new'
    CONTACTED = 'contacted'
    IN_PROGRESS = 'in_progress'
    CLOSED = 'closed'


class PropertyRequestCreateSchema(Schema):
    property_id: int
    request_type: RequestType
    message: Optional[str] = None


class PropertyRequestOut(Schema):
    id: int
    user_id: int
    user_name: str
    property_id: int
    property_title: str
    request_type: RequestType
    message: Optional[str] = None
    status: RequestStatus
    assigned_agent_id: Optional[int] = None
    created_at: datetime
    
    @staticmethod
    def resolve_user_name(obj):
        return obj.user.get_full_name() or obj.user.username
        
    @staticmethod
    def resolve_property_title(obj):
        return obj.property.title


class PropertyRequestUpdateSchema(Schema):
    status: Optional[RequestStatus] = None
    assigned_agent_id: Optional[int] = None
