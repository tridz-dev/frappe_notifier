import frappe
from firebase_admin import _apps, initialize_app
from typing import List
from frappe_notifier.frappe_notifier.doctype.fn_user_device_token.fn_user_device_token import deactivate_device_token
import json

SETTINGS_DOCTYPE = "Frappe Notifier Settings"
USER_TOKEN_DOCTYPE = "FN User Device Token"

class FirebaseInitializationError(Exception):
    """Raised when Firebase initialization fails"""
    pass

def initialize_firebase_app() -> None:
    """Initialize Firebase app with proper error handling"""
    try:
        if not _apps:
            firebase_config_json = frappe.db.get_single_value(SETTINGS_DOCTYPE, "firebase_config")
            if not firebase_config_json:
                raise FirebaseInitializationError("Firebase configuration not found in settings")
            
            try:
                firebase_config = frappe.parse_json(firebase_config_json)
            except Exception as e:
                raise FirebaseInitializationError(f"Invalid Firebase configuration JSON: {str(e)}")
            
            try:
                initialize_app(options=firebase_config)
            except Exception as e:
                raise FirebaseInitializationError(f"Failed to initialize Firebase app: {str(e)}")
    except Exception as e:
        # Re-raise to be caught by the decorator
        raise FirebaseInitializationError(f"Firebase initialization failed: {str(e)}")

def subscribe_tokens_to_topic(tokens: List[str], topic_name: str):
    """
    Subscribes a list of tokens to a Firebase topic.
    Raises an exception on failure, to be caught by the calling context.
    """
    if not tokens:
        return
    
    from firebase_admin import messaging
    response = messaging.subscribe_to_topic(tokens, topic_name)
    if response.failure_count > 0:
        errors = [e.reason for e in response.errors]
        errored_index = [e.index for e in response.errors]
        frappe.log_error(
            title="FCM Subscribe Debug",
            message=json.dumps({
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "errors": errors
            }, indent=2)
        )
        if errors:
            if errors[0] == "INVALID_ARGUMENT" or errors[0] == "UNREGISTERED":
                for i in errored_index:
                    deactivate_device_token(tokens[i])
            else:
                frappe.log_error(
                    title="FCM Subscribe topic error",
                    message=json.dumps({
                        "error": error,
                        "index": errored_index,
                        "tokens": [tokens[i] for i in errored_index]
                    }, indent=2)
                )
        if response.success_count == 0:
            raise Exception(f"Failed to subscribe any device to topic: {topic_name}. Errors: {errors}")

def unsubscribe_tokens_from_topic(tokens: List[str], topic_name: str):
    """
    Unsubscribes a list of tokens from a Firebase topic.
    Raises an exception on failure, to be caught by the calling context.
    """
    if not tokens:
        return

    from firebase_admin import messaging
    response = messaging.unsubscribe_from_topic(tokens, topic_name)
    if response.failure_count > 0:
        errors = [e.reason for e in response.errors]
        frappe.log_error(f"Partial failure unsubscribing from topic {topic_name}", str(errors))
        if response.success_count == 0:
            raise Exception(f"Failed to unsubscribe any device from topic: {topic_name}. Errors: {errors}")

def get_user_tokens(user_id: str, project_name: str = None, site_name: str = None) -> List[str]:
    """
    Get user FCM tokens.
    Can be filtered by project and site.
    """
    filters = {"user_id": user_id}
    if project_name:
        filters["project_name"] = project_name
    if site_name:
        filters["site_name"] = site_name

    try:
        data = frappe.db.get_all(
            USER_TOKEN_DOCTYPE,
            filters=filters,
            fields=["fcm_token"]
        )
        return [item["fcm_token"] for item in data if item.get("fcm_token")]
    except Exception as e:
        frappe.log_error(title="Failed to fetch user tokens", message=str(e))
        return [] # Return empty list on failure 