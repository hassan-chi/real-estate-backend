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


class EssentialsSchema(Schema):
    country: List[CountryOut]
    province: List[ProvinceOut]
    city: List[CityOut]