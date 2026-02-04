import hashlib
import secrets
from datetime import timedelta
from http import HTTPStatus

from cities_light.models import Country, Region, City
from django.db import transaction
from django.utils import timezone
from ninja import Router
from django.conf import settings
from core.api.auth import GlobalAuth, get_token_for_user
from core.api.schemas.auth import PhoneNumberSchema, VerificationCheckSchema, CompleteProfileIn, AuthOutSchema, UserOut, \
    CountryOut, ProvinceOut, CityOut, LoginSchema
from core.api.utils.messageOut import MessageOut
from core.models import PhoneOTP, CustomUser
from core.services.twilio_service import TwilioService

router = Router(tags=['Auth'])


@router.post("/login/", response={HTTPStatus.OK: LoginSchema, HTTPStatus.TOO_MANY_REQUESTS: MessageOut})
def login_start(request, payload: PhoneNumberSchema):
    phone = payload.phone_number

    # cooldown check — use LOGIN purpose consistently
    last = (
        PhoneOTP.objects
        .filter(phone=phone, purpose=PhoneOTP.Purpose.LOGIN, used_at__isnull=True)
        .order_by("-created_at")
        .first()
    )
    if last and (timezone.now() - last.created_at).total_seconds() < 60:
        return 429, MessageOut(title="TOO MANY REQUESTS", message="Please wait before requesting another code.")

    # invalidate old
    PhoneOTP.objects.filter(phone=phone, purpose=PhoneOTP.Purpose.LOGIN, used_at__isnull=True).update(
        used_at=timezone.now())

    challenge_token = secrets.token_urlsafe(32)
    challenge_hash = hashlib.sha256(challenge_token.encode("utf-8")).hexdigest()

    sid = None
    if not (getattr(settings, "OTP_TEST_MODE", False) and phone in getattr(settings, "OTP_WHITELIST", [])):
        twilio_service = TwilioService()
        sid = twilio_service.send_verification_code(phone)

    PhoneOTP.objects.create(
        phone=phone,
        purpose=PhoneOTP.Purpose.LOGIN,
        verification_sid=sid,  # can be None for whitelist
        challenge_hash=challenge_hash,
        expires_at=timezone.now() + timedelta(minutes=10),
    )

    return LoginSchema(token=challenge_token)


@router.post("/login/verify/", response={200: AuthOutSchema, 400: MessageOut})
def check_verification(request, payload: VerificationCheckSchema):
    chash = hashlib.sha256(payload.token.encode("utf-8")).hexdigest()

    otp = PhoneOTP.objects.filter(challenge_hash=chash, used_at__isnull=True).order_by("-created_at").first()
    if not otp or otp.is_expired:
        return 400, MessageOut(title="failed", message="OTP expired. Please request a new one.")

    phone = otp.phone

    # ✅ whitelist verification
    if getattr(settings, "OTP_TEST_MODE", False) and phone in getattr(settings, "OTP_WHITELIST", []):
        if payload.code != getattr(settings, "OTP_TEST_CODE", "00000"):
            return 400, MessageOut(title="failed", message="Invalid code.")
        status = "approved"
    else:
        twilio = TwilioService()
        status = twilio.check_verification_code(phone, payload.code)

    if status != "approved":
        return 400, MessageOut(title="failed", message="Invalid code.")

    with transaction.atomic():
        otp.mark_used()

        user, _ = CustomUser.objects.get_or_create(phone=phone)
        if not user.is_verified:
            user.is_verified = True
            user.save(update_fields=["is_verified"])

        token = get_token_for_user(request, user)

    return 200, AuthOutSchema(token=token , user_id=user.pk)


@router.post(
    "/profile/complete/",
    auth=GlobalAuth(),
    response={200: MessageOut, 400: MessageOut, 403: MessageOut},
)
def complete_profile(request, payload: CompleteProfileIn):
    user: CustomUser = request.user

    # 1) must be phone-verified (OTP already approved)
    if not user.is_verified:
        return 403, MessageOut(title="failed", message="Verify your phone first.")

    # 2) if already completed, you can either block or allow updates
    if getattr(user, "profile_completed", False):
        return 400, MessageOut(title="failed", message="Profile already completed.")

    # 3) validate username uniqueness
    username = payload.username.strip()
    if CustomUser.objects.filter(username__iexact=username).exclude(id=user.id).exists():
        return 400, MessageOut(title="failed", message="Username is already taken.")

    # 4) load location objects
    try:
        country = Country.objects.get(id=payload.country_id)
    except Country.DoesNotExist:
        return 400, MessageOut(title="failed", message="Country not found.")

    try:
        province = Region.objects.get(id=payload.province_id)
    except Region.DoesNotExist:
        return 400, MessageOut(title="failed", message="Province not found.")

    try:
        city = City.objects.get(id=payload.city_id)
    except City.DoesNotExist:
        return 400, MessageOut(title="failed", message="City not found.")

    # 5) validate relationships (important!)
    # Region has country_id
    if province.country_id != country.id:
        return 400, MessageOut(title="failed", message="Province does not belong to country.")

    # City has region_id (cities-light uses 'region' FK)
    if city.region_id != province.id:
        return 400, MessageOut(title="failed", message="City does not belong to province.")

    # 6) Update user
    with transaction.atomic():
        user.username = username
        if payload.email:
            user.email = payload.email

        user.country = country
        user.province = province
        user.city = city

        user.profile_completed = True
        user.save()
    return 200, MessageOut(
        title="success",
        message=f"Profile completed successfully."
    )


@router.get(
    "/me/",
    auth=GlobalAuth(),
    response={200: UserOut, 400: MessageOut},
)
def me(request):
    user: CustomUser = request.user
    return 200, UserOut(
        username=user.username,
        phone=user.phone,
        email=user.email,
        role=user.role,
        is_verified=user.is_verified,
        profile_completed=user.profile_completed,

        country=CountryOut(id=user.country.id, name=user.country.name) if user.country else None,
        province=ProvinceOut(id=user.province.id, name=user.province.name) if user.province else None,
        city=CityOut(id=user.city.id, name=user.city.name) if user.city else None,
    )
