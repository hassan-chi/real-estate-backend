from typing import List

from ninja import Schema

class CountryOut(Schema):
    id: int
    name: str

class ProvinceOut(Schema):
    id: int
    name: str

class CityOut(Schema):
    id: int
    name: str
    region_id: int

class CurrencyOut(Schema):
    id: int
    name: str
    code: str

class EssentialsSchema(Schema):
    country: List[CountryOut]
    province: List[ProvinceOut]
    city: List[CityOut]
    currency: List[CurrencyOut]


class LocationSearchOut(Schema):
    city_id: int
    city_name: str
    province_id: int
    province_name: str
    display_name: str