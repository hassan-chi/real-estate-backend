from __future__ import annotations

from datetime import datetime
from typing import Optional

from ninja import Schema
from pydantic import field_validator, Field, EmailStr, model_validator
from django.utils import timezone
from core.validators.phone_number_validator import validate_phone_us_uk_iq


class CountryOut(Schema):
    id: int
    name: str

class ProvinceOut(Schema):
    id: int
    name: str

class CityOut(Schema):
    id: int
    name: str

class LoginSchema(Schema):
    token: str

class PhoneNumberSchema(Schema):
    phone_number: str

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        try:
            return validate_phone_us_uk_iq(v)  # should return normalized E.164
        except Exception as e:
            raise ValueError(str(e))


class VerificationCheckSchema(Schema):
    token: str
    code: str


class CompleteProfileIn(Schema):
    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_.]+$",
        description="Letters/numbers/underscore/dot only",
    )
    email: Optional[EmailStr] = Field(default=None)

    country_id: int = Field(..., gt=0)
    province_id: int = Field(..., gt=0)  # Region
    city_id: int = Field(..., gt=0)


class SubscriptionOut(Schema):
    id: int
    plan: str
    is_active: bool = False
    expires_at: Optional[datetime] = None

    @model_validator(mode='after')
    def check_expiry(self):
        if self.expires_at and self.expires_at < timezone.now():
            self.is_active = False
        return self


class UserOut(Schema):
    id: int
    username: str
    phone: Optional[str]
    email: Optional[str]
    role: str
    avatar: Optional[str]
    is_verified: bool
    profile_completed: bool

    country: Optional[CountryOut]
    province: Optional[ProvinceOut]
    city: Optional[CityOut]
    
    subscription: Optional[SubscriptionOut] = None
    
    unread_notification_count: int = 0
    total_properties: int = 0
    total_sold_properties: int = 0
    total_rented_properties: int = 0
    total_active_listings: int = 0

class AuthOutSchema(Schema):
    token: str
    user_id: int


class UpdateProfileIn(Schema):
    username: Optional[str] = Field(
        None,
        min_length=3,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_.]+$",
        description="Letters/numbers/underscore/dot only",
    )
    email: Optional[EmailStr] = Field(default=None)

    country_id: Optional[int] = Field(None, gt=0)
    province_id: Optional[int] = Field(None, gt=0)
    city_id: Optional[int] = Field(None, gt=0)