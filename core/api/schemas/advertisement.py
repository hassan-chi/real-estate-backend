from datetime import datetime
from enum import Enum
from typing import Optional

from ninja import Schema


class AdPosition(str, Enum):
    HOME = 'home'
    SEARCH = 'search'
    DETAILS = 'details'


class AdvertisementOut(Schema):
    id: int
    title: str
    image: str
    position: AdPosition
    link: str
    start_date: datetime
    end_date: datetime
    
    @staticmethod
    def resolve_image(obj):
        if obj.image:
            return obj.image.url
        return None
