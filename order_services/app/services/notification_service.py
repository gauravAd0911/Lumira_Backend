# app/services/notification_service.py

import json
import logging
import smtplib
from email.message import EmailMessage

from twilio.base.exceptions import TwilioException
from twilio.rest import Client

from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Handles customer order notifications."""

    def __init__(self):
        self.client = None
        if settings.TWILIO_SID and settings.TWILIO_AUTH and settings.TWILIO_PHONE:
            self.client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH)

    def send_delivery_notifications(self, order) -> None:
        """Send SMS and email when an order is delivered.

        Notification failures are logged but never block the order status update.
        """
        if not settings.ENABLE_ORDER_NOTIFICATIONS:
            logger.info("Order notifications are disabled")
            return

        phone = self._phone_for_order(order)
        email = self._email_for_order(order)
        order_number = getattr(order, "order_number", "your order")

        if phone:
            self.send_delivery_sms(phone, order_number=order_number)
        else:
            logger.info("Skipping delivery SMS for order %s: no phone number", order_number)

        if email:
            self.send_delivery_email(email, order_number=order_number)
        else:
            logger.info("Skipping delivery email for order %s: no email address", order_number)

    def send_delivery_sms(self, phone: str, *, order_number: str | None = None) -> None:
        """Send delivery success SMS."""
        if not self.client:
            logger.warning("Skipping delivery SMS: Twilio credentials are not configured")
            return

        message = f"Your order {order_number or ''} has been delivered successfully. Thank you for shopping with Mahi Skin!".strip()
        try:
            self.client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE,
                to=phone,
            )
            logger.info("Delivery SMS sent for order %s", order_number)
        except TwilioException as exc:
            logger.error("Failed to send delivery SMS for order %s: %s", order_number, exc)

    def send_delivery_email(self, email: str, *, order_number: str | None = None) -> None:
        """Send delivery success email through SMTP."""
        if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
            logger.warning("Skipping delivery email: SMTP_HOST/SMTP_FROM_EMAIL are not configured")
            return

        subject = f"Order {order_number} delivered" if order_number else "Your order was delivered"
        body = (
            f"Hi,\n\nYour order {order_number or ''} has been delivered successfully.\n"
            "Thank you for shopping with Mahi Skin.\n"
        )

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = settings.SMTP_FROM_EMAIL
        message["To"] = email
        message.set_content(body)

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
                if settings.SMTP_USE_TLS:
                    smtp.starttls()
                if settings.SMTP_USER and settings.SMTP_PASS:
                    smtp.login(settings.SMTP_USER, settings.SMTP_PASS)
                smtp.send_message(message)
            logger.info("Delivery email sent for order %s", order_number)
        except (OSError, smtplib.SMTPException) as exc:
            logger.error("Failed to send delivery email for order %s: %s", order_number, exc)

    @staticmethod
    def _shipping_details(order) -> dict:
        raw_address = getattr(order, "shipping_address", None)
        if isinstance(raw_address, dict):
            return raw_address
        if isinstance(raw_address, str) and raw_address.strip():
            try:
                parsed = json.loads(raw_address)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                return {}
        return {}

    def _phone_for_order(self, order) -> str | None:
        details = self._shipping_details(order)
        phone = getattr(order, "guest_phone", None) or details.get("phone") or details.get("mobile")
        phone = str(phone or "").strip()
        return phone or None

    def _email_for_order(self, order) -> str | None:
        details = self._shipping_details(order)
        email = getattr(order, "guest_email", None) or details.get("email") or details.get("emailAddress")
        email = str(email or "").strip().lower()
        return email or None
