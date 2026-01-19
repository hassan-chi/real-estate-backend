import phonenumbers
from django.core.exceptions import ValidationError

ALLOWED_REGIONS = {"US", "GB", "IQ"}


def validate_phone_us_uk_iq(value: str) -> str:
    try:
        # Require +countrycode
        phone = phonenumbers.parse(value, None)

        if not phonenumbers.is_valid_number(phone):
            raise ValidationError("Invalid phone number.")

        region = phonenumbers.region_code_for_number(phone)
        if region not in ALLOWED_REGIONS:
            raise ValidationError(
                "Only US (+1), UK (+44), and Iraq (+964) numbers are allowed."
            )

        return phonenumbers.format_number(
            phone, phonenumbers.PhoneNumberFormat.E164
        )

    except phonenumbers.NumberParseException:
        raise ValidationError(
            "Invalid phone number. Use format like +1..., +44..., or +964..."
        )
