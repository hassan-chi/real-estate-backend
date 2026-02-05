from __future__ import annotations

from datetime import datetime
from typing import Optional

from ninja import Schema
from pydantic import field_validator, Field, EmailStr
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
    start_date: datetime
    end_date: Optional[datetime] = None  # NULL for per-listing plans
    active: bool
    created_at: datetime
    price: float
    plan: str
    listing_credits: int = 0
    used_credits: int = 0
    remaining_credits: int = 0
class UserOut(Schema):
    username: str
    phone: str
    email: Optional[str]
    role: str
    is_verified: bool
    profile_completed: bool
    country: Optional[CountryOut] = None
    province: Optional[ProvinceOut] = None
    city: Optional[CityOut] = None
    unread_notification_count: int = 0
    subscription: Optional[SubscriptionOut] = None
    total_properties: int = 0
    total_sold_properties: int = 0
    total_rented_properties: int = 0
    total_active_listings: int = 0

class AuthOutSchema(Schema):
    token: str
    user_id: int