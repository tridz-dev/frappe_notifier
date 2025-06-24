import frappe
import json
from typing import List, Dict, Any, Optional
from firebase_admin import messaging, exceptions, _apps, initialize_app
from frappe_notifier.utils.normalize_to_https import normalize_url_to_https


SETTINGS_DOCTYPE = "Frappe Notifier Settings"
USER_TOKEN_DOCTYPE = "FN User Device Token"
NOTIFICATION_LOG_DOCTYPE = "FN Notification Log"

class NotificationError(Exception):
    """Base exception for notification related errors"""
    pass

class FirebaseInitializationError(NotificationError):
    """Raised when Firebase initialization fails"""
    pass

class InvalidInputError(NotificationError):
    """Raised when input parameters are invalid"""
    pass

def create_notification_log(
    notification_type: str,
    title: str,
    body: str,
    notification_data: Dict[str, Any],
    status: str = "Pending",
    error_message: str = None
) -> str:
    """Create a notification log entry"""
    log = frappe.get_doc({
        "doctype": NOTIFICATION_LOG_DOCTYPE,
        "status": status,
        "notification_type": notification_type,
        "title": title,
        "body": body,
        "notification_data": json.dumps(notification_data),
        "error_message": error_message
    })
    log.insert()
    return log.name

def update_notification_log(
    log_name: str,
    status: str,
    error_message: str = None
) -> None:
    """Update a notification log entry"""
    log = frappe.get_doc(NOTIFICATION_LOG_DOCTYPE, log_name)
    log.status = status
    if error_message:
        log.error_message = error_message
    log.save()

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
        raise FirebaseInitializationError(f"Firebase initialization failed: {str(e)}")

def validate_notification_data(data: Dict[str, Any]) -> None:
    """Validate notification data"""
    # required_fields = ["base_url", "click_action"]
    # missing_fields = [field for field in required_fields if not data.get(field)]
    
    # if missing_fields:
    #     raise InvalidInputError(f"Missing required fields in notification data: {', '.join(missing_fields)}")
    pass

@frappe.whitelist()
def topic(topic_name: str, title: str, body: str, data: str) -> Dict[str, Any]:
    """Send notification to a topic"""
    log_name = None
    try:
        if not all([topic_name, title, body]):
            raise InvalidInputError("topic_name, title, and body are required parameters")

        # Create initial log entry
        log_name = create_notification_log(
            notification_type="topic",
            title=title,
            body=body,
            notification_data={
                "topic_name": topic_name,
                "data": data
            }
        )

        initialize_firebase_app()
        
        try:
            data_dict = json.loads(data)
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON data: {str(e)}"
            update_notification_log(log_name, "Failed", error_msg)
            raise InvalidInputError(error_msg)

        validate_notification_data(data_dict)
        
        # Normalize URLs
        if data_dict.get("base_url"):
            data_dict["base_url"] = normalize_url_to_https(data_dict["base_url"])
        if data_dict.get("click_action"):
            data_dict["click_action"] = normalize_url_to_https(data_dict["click_action"])

        notification_icon = data_dict.get("notification_icon", "")

        message = messaging.Message(
            webpush=messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    title=title,
                    body=body,
                    icon=notification_icon,
                ),
                fcm_options=messaging.WebpushFCMOptions(
                    link=data_dict.get("click_action")
                )
            ),
            topic=topic_name
        )

        try:
            response = messaging.send(message)
            update_notification_log(log_name, "Sent")
            return {"success": True, "message_id": response, "log_name": log_name}
        except exceptions.FirebaseError as e:
            error_msg = f"Failed to send topic notification: {str(e)}"
            update_notification_log(log_name, "Failed", error_msg)
            raise NotificationError(error_msg)

    except Exception as e:
        if log_name:
            update_notification_log(log_name, "Failed", str(e))
        raise

@frappe.whitelist()
def user(project_name: str, site_name: str, user_id: str, title: str, body: str, data: str) -> Dict[str, Any]:
    """Send notification to a user"""
    log_name = None
    try:
        if not all([project_name, site_name, user_id, title, body]):
            raise InvalidInputError("project_name, site_name, user_id, title, and body are required parameters")

        # Create initial log entry
        log_name = create_notification_log(
            notification_type="user",
            title=title,
            body=body,
            notification_data={
                "project_name": project_name,
                "site_name": site_name,
                "user_id": user_id,
                "data": data
            }
        )

        initialize_firebase_app()
        
        try:
            data_dict = json.loads(data)
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON data: {str(e)}"
            update_notification_log(log_name, "Failed", error_msg)
            raise InvalidInputError(error_msg)

        validate_notification_data(data_dict)
        
        # Normalize URLs
        if data_dict.get("base_url"):
            data_dict["base_url"] = normalize_url_to_https(data_dict["base_url"])
        if data_dict.get("click_action"):
            data_dict["click_action"] = normalize_url_to_https(data_dict["click_action"])

        tokens = user_tokens(project_name=project_name, site_name=site_name, user_id=user_id)
        if not tokens:
            error_msg = f"No device tokens found for user {user_id}"
            update_notification_log(log_name, "Failed", error_msg)
            return {"success": False, "message": error_msg, "log_name": log_name}

        notification_icon = data_dict.get("notification_icon", "")

        message = messaging.MulticastMessage(
            webpush=messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    title=title,
                    body=body,
                    icon=notification_icon,
                    badge="",
                    data={
                        "base_url": data_dict.get("base_url"),
                        "click_action": data_dict.get("click_action"),
                    },
                    custom_data={
                        "base_url": data_dict.get("base_url"),
                        "click_action": data_dict.get("click_action"),
                    }
                ),
                fcm_options=messaging.WebpushFCMOptions(
                    link=data_dict.get("click_action")
                )
            ),
            tokens=tokens
        )

        try:
            response = messaging.send_each_for_multicast(message)
            success_count = sum(1 for result in response.responses if result.success)
            failure_count = len(tokens) - success_count
            
            if failure_count > 0:
                error_msg = f"Some notifications failed. Success: {success_count}, Failures: {failure_count}"
                update_notification_log(log_name, "Failed", error_msg)
            else:
                update_notification_log(log_name, "Sent")
            
            return {
                "success": True,
                "success_count": success_count,
                "failure_count": failure_count,
                "log_name": log_name,
                "responses": [
                    {
                        "token": token,
                        "success": result.success,
                        "error": str(result.exception) if result.exception else None
                    }
                    for token, result in zip(tokens, response.responses)
                ]
            }
        except exceptions.FirebaseError as e:
            error_msg = f"Failed to send user notification: {str(e)}"
            update_notification_log(log_name, "Failed", error_msg)
            raise NotificationError(error_msg)

    except Exception as e:
        if log_name:
            update_notification_log(log_name, "Failed", str(e))
        raise

def user_tokens(project_name: str, site_name: str, user_id: str) -> List[str]:
    """Get user tokens with error handling"""
    try:
        data = frappe.db.get_all(
            USER_TOKEN_DOCTYPE,
            filters={
                "project_name": project_name,
                "site_name": site_name,
                "user_id": user_id
            },
            fields=["fcm_token"]
        )
        return [item["fcm_token"] for item in data if item.get("fcm_token")]
    except Exception as e:
        raise NotificationError(f"Failed to fetch user tokens: {str(e)}")
    


