from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, PropertyRequest, Property, Currency, PropertyImage, Amenity, Notification
from .services.onesignal_service import send_push_notification

from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import redirect
from django.utils.html import format_html
from admin_searchable_dropdown.filters import AutocompleteFilter


class OwnerFilter(AutocompleteFilter):
    title = "Owner"
    field_name = "owner"


class AmenityFilter(AutocompleteFilter):
    title = "Amenities"
    field_name = "amenities"


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
    fields = ("image", "is_cover", "order")
    ordering = ("order",)


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    autocomplete_fields = ("owner", "city", 'province')
    list_display = ("title", "owner", "status", "approved")
    list_filter = ("status", "approved", "property_type", OwnerFilter, 'amenities__name')
    search_fields = ("title", "owner__username")
    actions = ("approve_properties",)
    inlines = [PropertyImageInline]
    readonly_fields = ("approve_button",)

    def get_readonly_fields(self, request, obj=None):
        """
        Hide approve button on CREATE page
        """
        readonly = list(super().get_readonly_fields(request, obj))
        if obj is None and "approve_button" in readonly:
            readonly.remove("approve_button")
        return readonly

    def approve_properties(self, request, queryset):
        updated = queryset.update(approved=True)
        self.message_user(
            request,
            f"Approved {updated} properties.",
            messages.SUCCESS,
        )

    approve_properties.short_description = "Approve selected properties"

    def approve_button(self, obj):
        if not obj.approved:
            return format_html('<a class="button" href="../approve/">Approve</a>')
        return "Already Approved"

    approve_button.short_description = "Approve Property"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:object_id>/approve/",
                self.admin_site.admin_view(self.approve_property_view),
                name="property-approve",
            ),
        ]
        return custom_urls + urls

    def approve_property_view(self, request, object_id):
        obj = self.get_object(request, object_id)
        if not obj:
            self.message_user(request, "Property not found.", messages.ERROR)
            return redirect("../change/")

        if obj.approved:
            self.message_user(request, "Property already approved.", messages.INFO)
            return redirect("../change/")

        obj.approved = True
        obj.save(update_fields=["approved"])
        
        # Create notification for property owner
        notification = Notification.objects.create(
            user=obj.owner,
            notification_type=Notification.NotificationType.PROPERTY_APPROVED,
            title="Property Approved",
            message=f"Your property '{obj.title}' has been approved and is now visible to buyers.",
            related_property=obj,
        )
        
        # Send push notification
        result = send_push_notification(
            user_id=obj.owner.id,
            title=notification.title,
            message=notification.message,
            data={"type": "property_approved", "property_id": obj.id}
        )
        if result.get("success") and result.get("notification_id"):
            notification.is_pushed = True
            notification.onesignal_id = result["notification_id"]
            notification.save(update_fields=["is_pushed", "onesignal_id"])
        
        self.message_user(request, "Property approved successfully.", messages.SUCCESS)
        return redirect("../change/")

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = Property.objects.get(pk=obj.pk)
            old_status = old_obj.status
        else:
            old_status = None
        
        super().save_model(request, obj, form, change)
        
        # Check if status changed and create notification
        if change and old_status != obj.status:
            if obj.status == Property.PropertyStatus.SOLD:
                notification = Notification.objects.create(
                    user=obj.owner,
                    notification_type=Notification.NotificationType.PROPERTY_SOLD,
                    title="Property Sold",
                    message=f"Congratulations! Your property '{obj.title}' has been marked as sold.",
                    related_property=obj,
                )
                result = send_push_notification(
                    user_id=obj.owner.id,
                    title=notification.title,
                    message=notification.message,
                    data={"type": "property_sold", "property_id": obj.id}
                )
                if result.get("success") and result.get("notification_id"):
                    notification.is_pushed = True
                    notification.onesignal_id = result["notification_id"]
                    notification.save(update_fields=["is_pushed", "onesignal_id"])
                    
            elif obj.status == Property.PropertyStatus.RENTED:
                notification = Notification.objects.create(
                    user=obj.owner,
                    notification_type=Notification.NotificationType.PROPERTY_RENTED,
                    title="Property Rented",
                    message=f"Congratulations! Your property '{obj.title}' has been rented.",
                    related_property=obj,
                )
                result = send_push_notification(
                    user_id=obj.owner.id,
                    title=notification.title,
                    message=notification.message,
                    data={"type": "property_rented", "property_id": obj.id}
                )
                if result.get("success") and result.get("notification_id"):
                    notification.is_pushed = True
                    notification.onesignal_id = result["notification_id"]
                    notification.save(update_fields=["is_pushed", "onesignal_id"])


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    search_fields = ("phone", "email", "username")
    list_display = ("username", "email", "role", "is_staff", "is_verified")
    list_filter = ("role", "is_verified", "province", "city")
    ordering = ("-created_at",)

    # EDIT page (shows hashed password + "Change password" button)
    fieldsets = (
        (None, {"fields": ("username", "phone", "email", "password")}),
        ("Permissions", {"fields": ("role", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Status", {"fields": ("is_verified", "is_active", 'profile_completed')}),
    )

    # CREATE page (IMPORTANT: no "password" here)
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "phone", "email", "role", "password1", "password2"),
        }),
    )


@admin.register(PropertyRequest)
class PropertyRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'property', 'request_type', 'status', 'assigned_agent')
    list_filter = ('request_type', 'status', 'assigned_agent')
    search_fields = ('user__phone', 'property__title', 'user__username')
    autocomplete_fields = ('user', 'property', 'assigned_agent')

    def close_requests(self, request, queryset):
        queryset.update(status='closed')

    close_requests.short_description = "Mark selected requests as closed"

    actions = [close_requests]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.role == 'admin':
            return qs
        return qs.filter(assigned_agent=request.user)

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = PropertyRequest.objects.get(pk=obj.pk)
            old_status = old_obj.status
            old_agent = old_obj.assigned_agent
        else:
            old_status = None
            old_agent = None
        
        super().save_model(request, obj, form, change)
        
        # Notify user when request status changes
        if change and old_status != obj.status:
            notification = Notification.objects.create(
                user=obj.user,
                notification_type=Notification.NotificationType.REQUEST_STATUS_CHANGED,
                title="Request Status Updated",
                message=f"Your {obj.get_request_type_display()} request for '{obj.property.title}' is now {obj.get_status_display()}.",
                related_property=obj.property,
                related_request=obj,
            )
            result = send_push_notification(
                user_id=obj.user.id,
                title=notification.title,
                message=notification.message,
                data={"type": "request_status", "property_id": obj.property.id, "request_id": obj.id}
            )
            if result.get("success") and result.get("notification_id"):
                notification.is_pushed = True
                notification.onesignal_id = result["notification_id"]
                notification.save(update_fields=["is_pushed", "onesignal_id"])
        
        # Notify agent when assigned to a request
        if change and old_agent != obj.assigned_agent and obj.assigned_agent:
            notification = Notification.objects.create(
                user=obj.assigned_agent,
                notification_type=Notification.NotificationType.REQUEST_ASSIGNED,
                title="New Request Assigned",
                message=f"You have been assigned to handle a {obj.get_request_type_display()} request for '{obj.property.title}'.",
                related_property=obj.property,
                related_request=obj,
            )
            result = send_push_notification(
                user_id=obj.assigned_agent.id,
                title=notification.title,
                message=notification.message,
                data={"type": "request_assigned", "property_id": obj.property.id, "request_id": obj.id}
            )
            if result.get("success") and result.get("notification_id"):
                notification.is_pushed = True
                notification.onesignal_id = result["notification_id"]
                notification.save(update_fields=["is_pushed", "onesignal_id"])


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    listener_fields = ('code', "name")
    list_filter = ('code', 'name')
    search_fields = ('code', 'name')


@admin.register(Amenity)
class Admin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name',)
    list_filter = ('name',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "message" , "notification_type" , "is_pushed" , "is_read" , "onesignal_id")