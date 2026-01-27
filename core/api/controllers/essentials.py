from cities_light.models import Country, Region, City
from ninja import Router
from core.api.schemas.essentials import EssentialsSchema
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
