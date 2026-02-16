from datetime import datetime
from typing import List, Optional
from ninja import Schema
from pydantic import Field


class MessageOut(Schema):
    id: int
    text: str
    sender_id: int
    sender_name: str
    is_read: bool
    created_at: datetime
    
    @staticmethod
    def resolve_sender_name(obj):
        return obj.sender.get_full_name() or obj.sender.username


class ChatRoomOut(Schema):
    id: int
    partner_id: int
    partner_name: str
    property_id: Optional[int] = None
    property_title: Optional[str] = None
    property_image: Optional[str] = None
    last_message: Optional[MessageOut] = None
    last_message_text: Optional[str] = None
    last_message_is_read: Optional[bool] = None
    last_message_created_at: Optional[datetime] = None
    unread_count: int = 0



class SendMessageIn(Schema):
    text: str = Field(..., min_length=1)


class StartChatIn(Schema):
    property_id: int

