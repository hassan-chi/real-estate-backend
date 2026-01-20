from ninja import Router, Schema
from ..services.twilio_service import TwilioService
router = Router()

class PhoneNumberSchema(Schema):
    phone_number: str

class VerificationCheckSchema(Schema):
    phone_number: str
    code: str


@router.get("/health")
def mobile_health_check(request):
    return {"message": "API is healthy!", "type": "api"}

@router.post("/verification/send")
def send_verification(request, payload: PhoneNumberSchema):
    twilio_service = TwilioService()
    sid = twilio_service.send_verification_code(payload.phone_number)
    return {"sid": sid}

@router.post("/verification/check")
def check_verification(request, payload: VerificationCheckSchema):
    twilio_service = TwilioService()
    status = twilio_service.check_verification_code(payload.phone_number, payload.code)
    return {"status": status}

@router.get("/status")
def mobile_status(request):
    return {"status": "ok", "api": "api"}
