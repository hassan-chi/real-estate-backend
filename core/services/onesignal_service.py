import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class OneSignalService:
    """Service for sending push notifications via OneSignal REST API."""
    
    BASE_URL = "https://onesignal.com/api/v1"
    
    def __init__(self):
        self.app_id = settings.ONESIGNAL_APP_ID
        self.api_key = settings.ONESIGNAL_API_KEY
    
    @property
    def _headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.api_key}",
        }
    
    def send_to_user(self, user_id: int, title: str, message: str, data: dict = None) -> dict:
        """
        Send a push notification to a specific user by their external user id.
        
        Args:
            user_id: The user's database ID (used as external_user_id in OneSignal)
            title: Notification title
            message: Notification body message
            data: Optional additional data to send with the notification
            
        Returns:
            dict with 'success' boolean and 'response' or 'error' key
        """
        if not self.app_id or not self.api_key:
            logger.warning("OneSignal not configured. Skipping push notification.")
            return {"success": False, "error": "OneSignal not configured"}
        
        payload = {
            "app_id": self.app_id,
            "include_external_user_ids": [str(user_id)],
            "headings": {"en": title},
            "contents": {"en": message},
        }
        
        if data:
            payload["data"] = data
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/notifications",
                json=payload,
                headers=self._headers,
                timeout=10,
            )
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"OneSignal notification sent to user {user_id}: {result}")
            return {"success": True, "response": result, "notification_id": result.get("id")}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send OneSignal notification: {e}")
            return {"success": False, "error": str(e)}
    
    def send_to_users(self, user_ids: list, title: str, message: str, data: dict = None) -> dict:
        """
        Send a push notification to multiple users.
        
        Args:
            user_ids: List of user database IDs
            title: Notification title
            message: Notification body message
            data: Optional additional data
            
        Returns:
            dict with 'success' boolean and 'response' or 'error' key
        """
        if not self.app_id or not self.api_key:
            logger.warning("OneSignal not configured. Skipping push notification.")
            return {"success": False, "error": "OneSignal not configured"}
        
        payload = {
            "app_id": self.app_id,
            "include_external_user_ids": [str(uid) for uid in user_ids],
            "headings": {"en": title},
            "contents": {"en": message},
        }
        
        if data:
            payload["data"] = data
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/notifications",
                json=payload,
                headers=self._headers,
                timeout=10,
            )
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"OneSignal notification sent to {len(user_ids)} users: {result}")
            return {"success": True, "response": result, "notification_id": result.get("id")}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send OneSignal notification: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
onesignal_service = OneSignalService()


def send_push_notification(user_id: int, title: str, message: str, data: dict = None) -> dict:
    """Convenience function to send a push notification to a user."""
    return onesignal_service.send_to_user(user_id, title, message, data)
