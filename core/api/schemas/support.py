from ninja import Schema


class SupportOut(Schema):
    id: int
    title: str
    image: str
    link: str
    
    @staticmethod
    def resolve_image(obj):
        if obj.image:
            return obj.image.url
        return None
