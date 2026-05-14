import requests
from app.config import settings

class WhatsAppService:
    """Handles WhatsApp Business API notifications."""

    def __init__(self):
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.api_version = "v18.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    def send_message(self, to: str, message: str) -> bool:
        """Send text message via WhatsApp Business API."""
        try:
            # Remove any + prefix and ensure it's just numbers
            to_clean = to.lstrip('+')

            url = f"{self.base_url}/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            data = {
                "messaging_product": "whatsapp",
                "to": to_clean,
                "type": "text",
                "text": {
                    "body": message
                }
            }

            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()

            result = response.json()
            return result.get("messages", [{}])[0].get("id") is not None

        except Exception as e:
            print(f"WhatsApp message sending failed: {e}")
            return False

    def send_template_message(self, to: str, template_name: str, language_code: str = "en", components: list = None) -> bool: # type: ignore
        """Send template message via WhatsApp Business API."""
        try:
            to_clean = to.lstrip('+')

            url = f"{self.base_url}/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            data = {
                "messaging_product": "whatsapp",
                "to": to_clean,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": language_code
                    }
                }
            }

            if components:
                data["template"]["components"] = components

            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()

            result = response.json()
            return result.get("messages", [{}])[0].get("id") is not None

        except Exception as e:
            print(f"WhatsApp template message sending failed: {e}")
            return False