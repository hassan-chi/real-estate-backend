from typing import List
from django.db.models import Q, Max, Count, Prefetch
from django.forms import model_to_dict
from django.shortcuts import get_object_or_404
from ninja import Router
from core.api.auth import GlobalAuth
from core.api.schemas.chat import (
    ChatRoomOut, MessageOut, SendMessageIn, StartChatIn
)
from core.api.utils.messageOut import MessageOut as BasicMessage
from core.models import ChatRoom, Message, CustomUser, Notification, Property
from core.services.onesignal_service import send_push_notification

router = Router(tags=["chat"])


@router.get("/rooms", auth=GlobalAuth(), response=List[ChatRoomOut])
def get_chat_rooms(request):
    """Get all chat rooms for the authenticated user."""
    user = request.user
    
    rooms = ChatRoom.objects.filter(participants=user).select_related('property').prefetch_related('participants')
    
    response = []
    for room in rooms:
        partner = room.participants.exclude(id=user.id).first()
        if not partner:
            continue
            
        last_msg = Message.objects.filter(room=room).order_by('-created_at').first()
        unread = room.messages.filter(is_read=False).exclude(sender=user).count()
        
        response.append({
            "id": room.id,
            "partner_id": partner.id,
            "partner_name": partner.get_full_name() or partner.username,
            "property_id": room.property.id if room.property else None,
            "property_title": room.property.title if room.property else None,
            "property_image": None,
            "last_message": last_msg,
            "last_message_text": last_msg.text if last_msg else None,
            "last_message_is_read": last_msg.is_read if last_msg else None,
            "last_message_created_at": last_msg.created_at if last_msg else None,
            "unread_count": unread
        })

    return response


@router.post("/start", auth=GlobalAuth(), response=ChatRoomOut)
def start_chat(request, payload: StartChatIn):
    """Start a chat about a specific property."""
    user = request.user
    property_obj = get_object_or_404(Property, id=payload.property_id)
    
    partner = property_obj.owner
    if user.id == partner.id:
        return 400, {"message": "Cannot chat with yourself (you own this property)"}
        
    # Find existing room for this property and these participants
    # We use distinct() because filtering ManyToMany can return duplicates
    existing_room = ChatRoom.objects.filter(
        property=property_obj, 
        participants=user
    ).filter(participants=partner).distinct().first()
    
    if existing_room:
        room = existing_room
    else:
        room = ChatRoom.objects.create(property=property_obj)
        room.participants.add(user, partner)
        
    return {
        "id": room.id,
        "partner_id": partner.id,
        "partner_name": partner.get_full_name() or partner.username,
        "property_id": property_obj.id,
        "property_title": property_obj.title,
        "property_image": None,
        "last_message": None,
        "unread_count": 0
    }


@router.get("/rooms/{room_id}/messages", auth=GlobalAuth(), response=List[MessageOut])
def get_messages(request, room_id: int):
    """Get messages for a specific room."""
    user = request.user
    room = get_object_or_404(ChatRoom, id=room_id, participants=user)
    
    # Mark messages as read
    room.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)
    
    return room.messages.order_by('created_at')


@router.post("/rooms/{room_id}/messages", auth=GlobalAuth(), response=MessageOut)
def send_message(request, room_id: int, payload: SendMessageIn):
    """Send a message to a room."""
    user = request.user
    room = get_object_or_404(ChatRoom, id=room_id, participants=user)
    
    message = Message.objects.create(
        room=room,
        sender=user,
        text=payload.text
    )
    
    # Notify partner via OneSignal
    partner = room.participants.exclude(id=user.id).first()
    if partner:
        send_push_notification(
            user_id=partner.id,
            title=f"New message about {room.property.title}" if room.property else f"New message from {user.username}",
            message=payload.text[:50],  # Preview
            data={
                "type": "chat_message", 
                "room_id": room.id,
                "property_id": room.property.id if room.property else None
            }
        )
    
    return message
