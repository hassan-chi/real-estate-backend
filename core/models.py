from __future__ import annotations
import uuid
from datetime import timedelta

from cities_light.models import Country, Region, City
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from core.validators.phone_number_validator import validate_phone_us_uk_iq


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        USER = 'user', 'User'
        SELLER = 'seller', 'Seller'
        AGENT = 'agent', 'Agent'
        ADMIN = 'admin', 'Admin'

    phone = models.CharField(max_length=20, unique=True, null=True, blank=True,
                             help_text="US (+1), UK (+44), or Iraq (+964) only",
                             )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    province = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    profile_completed = models.BooleanField(default=False)

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        if self.phone:
            self.phone = validate_phone_us_uk_iq(self.phone)

        # If user is created with phone only, generate a username
        if not self.username:
            # Example: user_9647712345678_8f2a
            phone_part = (self.phone or "user").replace("+", "")
            self.username = f"user_{phone_part}_{uuid.uuid4().hex[:4]}"

        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        self.phone = validate_phone_us_uk_iq(self.phone)


class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=20)
    symbol = models.CharField(max_length=5)

    def __str__(self):
        return self.code


class Amenity(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon = models.ImageField(upload_to='amenities/', blank=True, null=True)

    def __str__(self):
        return self.name

class Property(models.Model):
    class PropertyType(models.TextChoices):
        APARTMENT = 'apartment', 'Apartment'
        HOUSE = 'house', 'House'
        LAND = 'land', 'Land'
        COMMERCIAL = 'commercial', 'Commercial'

    class ListingType(models.TextChoices):
        SALE = 'sale', 'For Sale'
        RENT = 'rent', 'For Rent'

    class PropertyStatus(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        SOLD = 'sold', 'Sold'
        RENTED = 'rented', 'Rented'

    title = models.CharField(max_length=255)
    description = models.TextField()
    property_type = models.CharField(max_length=20, choices=PropertyType.choices)
    listing_type = models.CharField(max_length=10, choices=ListingType.choices)
    price = models.IntegerField(validators=[
        MinValueValidator(1)
    ])
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    province = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=PropertyStatus.choices, default=PropertyStatus.AVAILABLE)
    approved = models.BooleanField(default=False)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='properties')
    bedrooms = models.PositiveIntegerField(default=1)
    bathrooms = models.PositiveIntegerField(default=1)
    area = models.PositiveIntegerField(help_text="in square meters", default=0)
    restrooms = models.PositiveIntegerField(default=1)
    balconies = models.PositiveIntegerField(default=1)
    furnished = models.BooleanField(default=False)
    amenities = models.ManyToManyField(Amenity, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title



class PropertyRequest(models.Model):
    class RequestType(models.TextChoices):
        PURCHASE = 'purchase', 'Purchase'
        RENT = 'rent', 'Rent'
        CALL = 'call', 'Call Request'
        DETAILS = 'details', 'Request Details'

    class RequestStatus(models.TextChoices):
        NEW = 'new', 'New'
        CONTACTED = 'contacted', 'Contacted'
        IN_PROGRESS = 'in_progress', 'In Progress'
        CLOSED = 'closed', 'Closed'

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='property_requests')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='requests')
    request_type = models.CharField(max_length=10, choices=RequestType.choices)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=12, choices=RequestStatus.choices, default=RequestStatus.NEW)
    assigned_agent = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='assigned_requests')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.get_request_type_display()} for {self.property.title} by {self.user.username}'


class Subscription(models.Model):
    class Plan(models.TextChoices):
        MONTHLY = 'monthly', 'Monthly'
        PERLISTING = 'perlisting', 'Per Listing'
        YEARLY = 'yearly', 'Yearly'

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='seller_subscriptions')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)  # NULL for per-listing plans
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    plan = models.CharField(max_length=20, choices=Plan.choices)
    
    # For per-listing plans
    listing_credits = models.PositiveIntegerField(default=0, help_text="Total purchased listing credits")
    used_credits = models.PositiveIntegerField(default=0, help_text="Credits used for listings")

    def __str__(self):
        return f'{self.user.username} - {self.get_plan_display()}'
    
    @property
    def remaining_credits(self):
        """Get remaining listing credits for per-listing plans."""
        return self.listing_credits - self.used_credits
    
    def can_create_listing(self):
        """Check if user can create a new listing based on subscription."""
        if not self.active:
            return False
        
        if self.plan == self.Plan.PERLISTING:
            return self.remaining_credits > 0
        else:
            # Time-based plans (monthly/yearly)
            return self.end_date and self.end_date >= timezone.now()
    
    def use_credit(self):
        """Deduct one credit for per-listing plans. Call after creating a property."""
        if self.plan == self.Plan.PERLISTING:
            self.used_credits += 1
            if self.used_credits >= self.listing_credits:
                self.active = False
            self.save(update_fields=['used_credits', 'active'])

class Advertisement(models.Model):
    class POSTITON(models.TextChoices):
        HOME = 'home', 'Home'
        SEARCH = 'search', 'Search'
        DETAILS = 'details', 'Details'
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='advertisements')
    position = models.CharField(max_length=20, choices=POSTITON.choices)
    link = models.URLField()
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)


class Support(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='support/')
    link = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class PhoneOTP(models.Model):
    class Purpose(models.TextChoices):
        REGISTER = "register", "Register"
        RESET = "reset", "Reset Password"
        LOGIN = "login", "Login"

    phone = models.CharField(max_length=20, db_index=True)
    purpose = models.CharField(
        max_length=20,
        choices=Purpose.choices,
        db_index=True,
    )

    challenge_hash = models.CharField(max_length=64, unique=True, db_index=True , default="")

    # Twilio Verify
    provider = models.CharField(max_length=20, default="twilio")
    verification_sid = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Twilio Verify SID",
        null=True,
    )

    expires_at = models.DateTimeField(db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["phone", "purpose", "expires_at"]),
            models.Index(fields=["phone", "purpose", "used_at"]),
            models.Index(fields=["verification_sid"]),
        ]

    def __str__(self) -> str:
        return f"{self.phone} ({self.purpose})"

    # ---------- State helpers ----------

    @property
    def is_used(self) -> bool:
        return self.used_at is not None

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    def mark_used(self) -> None:
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])

    # ---------- Factory ----------

    @classmethod
    def create_with_sid(
            cls,
            *,
            phone: str,
            purpose: str,
            verification_sid: str,
            ttl_minutes: int = 5,
            provider: str = "twilio",
    ) -> "PhoneOTP":
        """
        Create an OTP record that references a Twilio Verify SID.
        """
        expires_at = timezone.now() + timedelta(minutes=ttl_minutes)

        return cls.objects.create(
            phone=phone,
            purpose=purpose,
            provider=provider,
            verification_sid=verification_sid,
            expires_at=expires_at,
        )


class PropertyImage(models.Model):
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="properties/%Y/%m/%d/")
    order = models.PositiveIntegerField(default=0)
    is_cover = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"Image for {self.property_id}"


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        # Property-related
        PROPERTY_SOLD = 'property_sold', 'Property Sold'
        PROPERTY_RENTED = 'property_rented', 'Property Rented'
        PROPERTY_APPROVED = 'property_approved', 'Property Approved'
        PROPERTY_REJECTED = 'property_rejected', 'Property Rejected'
        
        # Request-related
        NEW_REQUEST = 'new_request', 'New Property Request'
        REQUEST_STATUS_CHANGED = 'request_status', 'Request Status Changed'
        REQUEST_ASSIGNED = 'request_assigned', 'Request Assigned to Agent'
        
        # Subscription-related
        SUBSCRIPTION_EXPIRING = 'sub_expiring', 'Subscription Expiring Soon'
        SUBSCRIPTION_EXPIRED = 'sub_expired', 'Subscription Expired'
        
        # General
        SYSTEM = 'system', 'System Notification'
        PROMO = 'promo', 'Promotional'

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NotificationType.choices)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Related objects for deep linking
    related_property = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True)
    related_request = models.ForeignKey(PropertyRequest, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Read tracking
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Push notification tracking
    is_pushed = models.BooleanField(default=False)
    onesignal_id = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.user.username}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
