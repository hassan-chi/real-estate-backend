from enum import Enum
from typing import List, Optional, Union

from ninja import Schema, Field
from pydantic import model_validator, field_validator
from core.api.schemas.pagination import PaginatedResponse


class PropertyType(str, Enum):
    APARTMENT = 'apartment'
    HOUSE = 'house'
    LAND = 'land'
    COMMERCIAL = 'commercial'


class ListingType(str, Enum):
    SALE = 'sale'
    RENT = 'rent'


class PropertyImageOut(Schema):
    id: int
    url: str
    is_cover: bool
    order: int


class CurrencyOut(Schema):
    id: int
    code: str
    name: str
    symbol: str


class AmenityOut(Schema):
    id: int
    name: str
    icon: Optional[str] = None

    @staticmethod
    def resolve_icon(obj) -> Optional[str]:
        if obj.icon:
            return obj.icon.url
        return None


class PropertyOut(Schema):
    id: int
    title: str
    description: str
    property_type: PropertyType
    listing_type: ListingType
    price: int
    currency: CurrencyOut
    province: str
    province_id: int
    city: str
    city_id: int
    bedrooms: int
    bathrooms: int
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    area: int
    restrooms: int
    balconies: int
    furnished: bool
    amenities: List[AmenityOut]
    images: List[PropertyImageOut]

    @staticmethod
    def resolve_images(obj) -> List[PropertyImageOut]:
        return [
            PropertyImageOut(
                id=image.id,
                url=image.image.url,
                is_cover=image.is_cover,
                order=image.order
            ) for image in obj.images.all()
        ]
    @staticmethod
    def resolve_province(obj) -> str:
        return obj.province.name

    @staticmethod
    def resolve_province_id(obj) -> int:
        return obj.province.id
    
    @staticmethod
    def resolve_city(obj) -> str:
        return obj.city.name
    
    @staticmethod
    def resolve_city_id(obj) -> int:
        return obj.city.id
    @staticmethod
    def resolve_amenities(obj) -> List[AmenityOut]:
        return [
            AmenityOut(
                id=amenity.id,
                name=amenity.name,
                icon=amenity.icon.url if amenity.icon else None
            ) for amenity in obj.amenities.all()
        ]


class PropertyFilterSchema(Schema):
    search: Optional[str] = None
    property_type: Optional[PropertyType] = None
    province_id: Optional[int] = Field(None, description="Filter by province")
    city_id: Optional[int] = Field(None, description="Filter by city")
    listing_type: Optional[ListingType] = Field(None, description="Filter by listing type (rent/sale)")
    min_price: Optional[int] = Field(None, ge=0, description="Minimum price")
    max_price: Optional[int] = Field(None, ge=0, description="Maximum price")
    bedrooms: Optional[int] = Field(None, ge=0, description="Minimum number of bedrooms")
    amenities: Optional[List[int]] = Field(None, description="List of amenity IDs")

    @model_validator(mode='after')
    def check_prices(self):
        if self.min_price is not None and self.max_price is not None and self.max_price < self.min_price:
            raise ValueError("max_price cannot be less than min_price")
        return self


class PropertyCreateSchema(Schema):
    title: str
    description: str
    property_type: PropertyType
    listing_type: ListingType
    price: int
    currency_id: int
    province_id: int
    city_id: int
    longitude: float
    latitude: float
    bedrooms: int
    bathrooms: int
    area: int
    restrooms: int
    balconies: int
    furnished: bool
    amenity_ids: str


class PropertyUpdateSchema(Schema):
    title: Optional[str] = None
    description: Optional[str] = None
    property_type: Optional[PropertyType] = None
    listing_type: Optional[ListingType] = None
    price: Optional[int] = None
    currency_id: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area: Optional[int] = None
    province_id: Optional[int] = None
    city_id: Optional[int] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    restrooms: Optional[int] = None
    balconies: Optional[int] = None
    furnished: Optional[bool] = False
    amenity_ids: Optional[List[int]] = None



class ImageReorderSchema(Schema):
    image_id: int = Field(..., description="Image ID to move")
    new_position: int = Field(..., ge=0, description="New position (0-indexed, other images will shift)")


PaginatedPropertyOut = PaginatedResponse[PropertyOut]




