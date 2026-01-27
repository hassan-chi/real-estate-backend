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