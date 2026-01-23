from cities_light.models import Country, Region, City
from ninja import Router
from core.api.schemas.essentials import EssentialsSchema

router = Router(tags=["essentials"])

@router.get("/", response={200: EssentialsSchema})
def get_essentials(request):
    countries = Country.objects.all().only("id", "name")
    provinces = Region.objects.all().only("id", "name")
    cities = City.objects.all().only("id", "name")

    return {
        "country": [{"id": c.id, "name": c.name} for c in countries],
        "province": [{"id": p.id, "name": p.name} for p in provinces],
        "city": [{"id": ct.id, "name": ct.name} for ct in cities],
    }
