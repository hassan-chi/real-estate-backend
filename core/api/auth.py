from django.conf import settings
from jose import jwt, JWTError
from ninja.security import HttpBearer

from core.models import CustomUser



def get_token_for_user(request, user):
    token = jwt.encode({'pk': str(user.pk)}, key=settings.SECRET_KEY,
                       algorithm='HS256')
    request.user = user
    return str(token)


def decode_token(token):
    return jwt.decode(token=token, key=settings.SECRET_KEY, algorithms=['HS256'])


class GlobalAuth(HttpBearer):
    header: str = "Authorization"
    def authenticate(self, request, token):
        try:
            user_pk = decode_token(token)
        except JWTError as e:
            return e
        try:
            if user := CustomUser.objects.get(pk=user_pk.get("pk", None), is_active=True):
                request.user = user
                return {"user": user, "token": token}
        except CustomUser.DoesNotExist:
            return None
