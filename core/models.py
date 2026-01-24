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
    location = models.JSONField()  # For lat/lng
    status = models.CharField(max_length=10, choices=PropertyStatus.choices, default=PropertyStatus.AVAILABLE)
    approved = models.BooleanField(default=False)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='properties')
    bedrooms = models.PositiveIntegerField(default=1)
    bathrooms = models.PositiveIntegerField(default=1)
    area = models.PositiveIntegerField(help_text="in square meters", default=0) # in square meters
    amenities = models.ManyToManyField(Amenity, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title



class PropertyRequest(models.Model):
    class RequestType(models.TextChoices):
        VIEWING = 'viewing', 'Viewing'
        INQUIRY = 'inquiry', 'Inquiry'

    class RequestStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'
        CLOSED = 'closed', 'Closed'

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='property_requests')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='requests')
    request_type = models.CharField(max_length=10, choices=RequestType.choices)
    status = models.CharField(max_length=10, choices=RequestStatus.choices, default=RequestStatus.PENDING)
    assigned_agent = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='agent_requests')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.get_request_type_display()} for {self.property.title} by {self.user.username}'




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
