try:
    import africastalking
except ImportError:
    africastalking = None

from app.core.config import get_settings
import random

settings = get_settings()


class SMSService:
    def __init__(self):
        self.username = settings.AFRICASTALKING_USERNAME
        self.api_key = settings.AFRICASTALKING_API_KEY
        self.sender_id = settings.AFRICASTALKING_SENDER_ID
        
        if self.api_key and africastalking:
            africastalking.initialize(self.username, self.api_key)
            self.sms = africastalking.SMS
        else:
            self.sms = None

    def generate_otp(self) -> str:
        return str(random.randint(100000, 999999))

    def send_otp(self, phone: str, otp: str) -> bool:
        if not self.sms:
            print(f"[SMS MOCK] Sending OTP {otp} to {phone}")
            return True
        
        try:
            formatted_phone = self._format_phone(phone)
            message = f"Your SafeInvest OTP is {otp}. Valid for 10 minutes. Do not share."
            response = self.sms.send(message, [formatted_phone], self.sender_id)
            return response["SMSMessageData"]["Recipients"][0]["status"] == "Success"
        except Exception as e:
            print(f"SMS Error: {e}")
            return False

    def _format_phone(self, phone: str) -> str:
        phone = phone.strip().replace(" ", "").replace("-", "")
        if phone.startswith("0"):
            phone = "254" + phone[1:]
        elif phone.startswith("+254"):
            phone = phone[1:]
        elif not phone.startswith("254"):
            phone = "254" + phone
        return "+" + phone


sms_service = SMSService()