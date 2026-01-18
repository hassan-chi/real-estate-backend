from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        USER = 'user', 'User'
        SELLER = 'seller', 'Seller'
        AGENT = 'agent', 'Agent'
        ADMIN = 'admin', 'Admin'

    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    province = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


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
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    location = models.JSONField()  # For lat/lng
    status = models.CharField(max_length=10, choices=PropertyStatus.choices, default=PropertyStatus.AVAILABLE)
    approved = models.BooleanField(default=False)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='properties')
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
        return f'{self.get_request_type_display()} for {self.property.title} by {self.user.full_name}'