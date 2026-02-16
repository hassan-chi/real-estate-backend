from cities_light.models import Country, Region, City
from typing import List
from django.db.models import Q
from ninja import Router
from core.api.schemas.essentials import EssentialsSchema, LocationSearchOut
from core.models import Currency
router = Router(tags=["essentials"])

@router.get("/", response={200: EssentialsSchema})
def get_essentials(request):
    countries = Country.objects.all().only("id", "name")
    provinces = Region.objects.all().only("id", "name")
    cities = City.objects.all().only("id", "name" , "region_id")
    currency = Currency.objects.all().only("id", "name" , "code")

    return {
        "country": [{"id": c.id, "name": c.name} for c in countries],
        "province": [{"id": p.id, "name": p.name} for p in provinces],
        "city": [{"id": ct.id, "name": ct.name , "region_id" : ct.region_id} for ct in cities],
        "currency" : [{"id": ct.id, "name": ct.name , "code" : ct.code} for ct in currency],
    }


@router.get("/search", response=List[LocationSearchOut])
def search_locations(request, query: str = ""):
    """Search cities and provinces by name. Returns 'City, Province' format."""
    if not query or len(query) < 2:
        return []
    
    cities = City.objects.filter(
        Q(name__icontains=query) | Q(region__name__icontains=query)
    ).select_related('region').only('id', 'name', 'region__id', 'region__name')[:20]
    
    return [
        {
            "city_id": city.id,
            "city_name": city.name,
            "province_id": city.region.id,
            "province_name": city.region.name,
            "display_name": f"{city.name}, {city.region.name}"
        }
        for city in cities
    ]

