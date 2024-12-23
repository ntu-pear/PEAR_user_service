from twilio.rest import Client
from fastapi import APIRouter

import vonage

client = vonage.Client(key=#insert key, secret=#insert secret)
verify = vonage.Verify(client)

router = APIRouter()

# Request 2FA Code (Twilio)
# 0.0435 per SMS, $20 minimum for verification
@router.post("/request-2fa-code/")
async def request_2fa_code(account_sid: str, auth_token: str, service_sid: str, phone_no: str):
    client = Client(account_sid, auth_token)
    verification = client.verify \
        .v2 \
        .services(service_sid) \
        .verifications \
        .create(to=phone_no, channel='sms')
    
    print(verification.sid)
    return {"msg": "2FA sent"}

# Verify 2FA Code (Twilio)
@router.get("/verify-2fa-code/")
async def verify_2fa_code(account_sid: str, auth_token: str, service_sid: str, phone_no: str, code: int):
    client = Client(account_sid, auth_token)
    verification_check = client.verify \
        .v2 \
        .services(service_sid) \
        .verification_checks \
        .create(to=phone_no, code=code)

    print(verification_check.status)
    return {"msg": "2FA verified"}

# Request 2FA Code (Vonage)
# 0.0437 per SMS
@router.post("/request-2fa-code-2/")
async def request_2fa_code(phone_no: str):
    response = verify.start_verification(number=phone_no, brand="AcmeInc")

    if response["status"] == "0":
        print("Started verification request_id is %s" % (response["request_id"]))
    else:
        print("Error: %s" % response["error_text"])
        
    return {"msg": "2FA sent"}

# Verify 2FA Code (Vonage)
@router.get("/verify-2fa-code-2/")
async def verify_2fa_code(request_id: str, code: int):
    response = verify.check(request_id, code=code)
    if response["status"] == "0":
        print("Verification successful, event_id is %s" % (response["event_id"]))
    else:
        print("Error: %s" % response["error_text"])
        
    return {"msg": "2FA verified"}