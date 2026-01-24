from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, PropertyRequest, Property, Currency, PropertyImage

from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import redirect
from django.utils.html import format_html
from admin_searchable_dropdown.filters import AutocompleteFilter


class OwnerFilter(AutocompleteFilter):
    title = "Owner"
    field_name = "owner"

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
    fields = ("image", "is_cover", "order")
    ordering = ("order",)

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    autocomplete_fields = ("owner",)
    list_display = ("title", "owner", "status", "approved")
    list_filter = ("status", "approved", "property_type", OwnerFilter)
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
        self.message_user(request, "Property approved successfully.", messages.SUCCESS)
        return redirect("../change/")


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
        ("Status", {"fields": ("is_verified", "is_active" , 'profile_completed')}),
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


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    listener_fields = ('code', "name")
    list_filter = ('code', 'name')
    search_fields = ('code', 'name')




