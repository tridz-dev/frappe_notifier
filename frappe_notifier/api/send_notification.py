import frappe
import json
from typing import List, Dict, Any, Optional
from firebase_admin import messaging, exceptions, _apps, initialize_app
from frappe_notifier.utils.normalize_to_https import normalize_url_to_https
from frappe_notifier.utils.normalize_topic_name import normalize_topic_name
from frappe_notifier.utils.firebase import initialize_firebase_app, get_user_tokens
from frappe_notifier.frappe_notifier.doctype.fn_notification_topic.fn_notification_topic import get_channel_tokens_exclue_sender
from frappe_notifier.frappe_notifier.doctype.fn_user_device_token.fn_user_device_token import deactivate_device_token


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

def validate_notification_data(data: Dict[str, Any]) -> None:
    """Validate notification data"""
    # required_fields = ["base_url", "click_action"]
    # missing_fields = [field for field in required_fields if not data.get(field)]
    
    # if missing_fields:
    #     raise InvalidInputError(f"Missing required fields in notification data: {', '.join(missing_fields)}")
    pass

def send_notification(
    tokens: List[str],
    title: str,
    body: str | None,
    notification_icon: str = "",
    click_action: Optional[str] = None,
    base_url: Optional[str] = None,
    deactivate_invalid_tokens: bool = False
) -> Dict[str, Any]:
    """
    Send multicast notification and handle errors.
    
    Args:
        tokens: List of device tokens to send notification to
        title: Notification title
        body: Notification body (optional)
        notification_icon: Icon URL for notification
        click_action: Optional click action URL
        base_url: Optional base URL
        deactivate_invalid_tokens: Whether to deactivate invalid tokens (for user notifications)
    
    Returns:
        Dictionary with success status, counts, and response details
    """
    if not tokens:
        return {
            "success": False,
            "success_count": 0,
            "failure_count": 0,
            "responses": []
        }
    
    # Build notification data
    notification_data = {}
    if base_url:
        notification_data["base_url"] = base_url
    if click_action:
        notification_data["click_action"] = click_action
    
    # Build webpush config
    webpush_notification = messaging.WebpushNotification(
        title=title,
        body=body or "",
        icon=notification_icon,
    )
    
    # Add additional fields for user notifications
    if click_action or base_url:
        webpush_notification.badge = ""
        webpush_notification.data = notification_data
        webpush_notification.custom_data = notification_data
    
    webpush_config = messaging.WebpushConfig(
        notification=webpush_notification,
    )
    
    # Add FCM options if click_action is provided
    if click_action:
        webpush_config.fcm_options = messaging.WebpushFCMOptions(
            link=click_action
        )
    
    message = messaging.MulticastMessage(
        webpush=webpush_config,
        tokens=tokens
    )
    
    try:
        response = messaging.send_each_for_multicast(message)
        success_count = sum(1 for result in response.responses if result.success)
        failure_count = len(tokens) - success_count
        
        # Handle invalid tokens if enabled
        if deactivate_invalid_tokens and failure_count > 0:
            for token, result in zip(tokens, response.responses):
                error = str(result.exception) if result.exception else None
                if not result.success and error:
                    if (
                        "NotRegistered" in error or
                        "Requested entity was not found" in error
                    ):
                        deactivate_device_token(token)
                    else:
                        frappe.log_error(
                            title="FCM Multicast Error",
                            message=json.dumps({
                                "token": token,
                                "error": error
                            }, indent=2)
                        )
        
        # Log detailed debug info for failures (user notifications)
        if deactivate_invalid_tokens and failure_count > 0:
            frappe.log_error(
                title="FCM Multicast Debug",
                message=json.dumps({
                    "success_count": response.success_count,
                    "failure_count": response.failure_count,
                    "results": [
                        {
                            "success": r.success,
                            "error": str(r.exception) if r.exception else None,
                            "message_id": r.message_id
                        }
                        for r in response.responses
                    ]
                }, indent=2)
            )
        
        return {
            "success": failure_count == 0,
            "success_count": success_count,
            "failure_count": failure_count,
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
        error_msg = f"Failed to send notification: {str(e)}"
        raise NotificationError(error_msg)

@frappe.whitelist()
def topic(topic_name: str, title: str, body: str | None, data: str) -> Dict[str, Any]:
    """Send notification to a topic"""
    log_name = None
    try:
        if not all([topic_name, title]):
            raise InvalidInputError("topic_name and title are required parameters")

        topic_name=normalize_topic_name(topic_name)
        # Create initial log entry
        log_name = create_notification_log(
            notification_type="topic",
            title=title,
            body=body or "",
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
        channel_tokens = get_channel_tokens_exclue_sender(topic_name,data_dict.get("from_user"))
        if not channel_tokens:
            error_msg = f"No device tokens found for channel {topic_name}"
            update_notification_log(log_name, "Failed", error_msg)
            return {"success": False, "message": error_msg, "log_name": log_name}

        response = send_notification(
            tokens=channel_tokens,
            title=title,
            body=body,
            notification_icon=notification_icon,
            click_action=None,
            base_url=None,
            deactivate_invalid_tokens=True
        )
        
        if response["failure_count"] > 0:
            error_msg = f"Some notifications failed. Success: {response['success_count']}, Failures: {response['failure_count']}"
            update_notification_log(log_name, "Failed", error_msg)
        else:
            update_notification_log(log_name, "Sent")
        
        return {
            "success": True,
            "log_name": log_name
        }

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

        tokens = get_user_tokens(project_name=project_name, site_name=site_name, user_id=user_id)
        if not tokens:
            error_msg = f"No device tokens found for user {user_id}"
            update_notification_log(log_name, "Failed", error_msg)
            return {"success": False, "message": error_msg, "log_name": log_name}

        notification_icon = data_dict.get("notification_icon", "")

        response = send_notification(
            tokens=tokens,
            title=title,
            body=body,
            notification_icon=notification_icon,
            click_action=data_dict.get("click_action"),
            base_url=data_dict.get("base_url"),
            deactivate_invalid_tokens=True
        )
        
        if response["failure_count"] > 0:
            error_msg = f"Some notifications failed. Success: {response['success_count']}, Failures: {response['failure_count']}"
            update_notification_log(log_name, "Failed", error_msg)
        else:
            update_notification_log(log_name, "Sent")
        
        return {
            "success": True,
            "success_count": response["success_count"],
            "failure_count": response["failure_count"],
            "log_name": log_name,
            "responses": response["responses"]
        }

    except Exception as e:
        if log_name:
            update_notification_log(log_name, "Failed", str(e))
        raise