# apps/notifications/services.py 
"""Service de notifications Twilio""" 
from django.conf import settings 
from twilio.rest import Client 
import logging 
 
logger = logging.getLogger(__name__) 
 
class TwilioService: 
    def __init__(self): 
        self.client = Client( 
            settings.TWILIO_ACCOUNT_SID, 
            settings.TWILIO_AUTH_TOKEN 
        ) 
 
    def send_sms(self, to, message): 
        """Envoie un SMS via Twilio""" 
        try: 
            message = self.client.messages.create( 
                body=message, 
                from_=settings.TWILIO_PHONE_NUMBER, 
                to=to 
            ) 
            return message.sid 
        except Exception as e: 
            logger.error(f"Erreur envoi SMS: {e}") 
            return None 
