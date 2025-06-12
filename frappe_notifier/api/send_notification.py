import frappe
import json
from firebase_admin import messaging, exceptions, _apps, initialize_app
from frappe_notifier.utils.normalize_to_https import normalize_url_to_https

USER_TOKEN_DOCTYPE="Frappe Notifier Settings"

def initialize_firebase_app():
    if not _apps:
        firebase_config_json=frappe.db.get_single_value(USER_TOKEN_DOCTYPE,"firebase_config");
        firebase_config=frappe.parse_json(firebase_config_json)
        initialize_app(options=firebase_config)

@frappe.whitelist()
def topic(topic_name,title,body,data):
    initialize_firebase_app()
    try:
        data_dict=json.loads(data)
    except json.JSONDecodeError:
        frappe.error_log(f"Error in parsing push notification data")

    notification_icon = data_dict.get("notification_icon") or ""

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

@frappe.whitelist()                       
def user(project_name,site_name,user_id,title,body,data):
    initialize_firebase_app()
    try:
        data_dict=json.loads(data)
    except json.JSONDecodeError:
        frappe.error_log(f"Error in parsing push notification data")
    
    # Normalize URLs
    data_dict["base_url"] = normalize_url_to_https(data_dict["base_url"])
    data_dict["click_action"] = normalize_url_to_https(data_dict["click_action"])

    tokens=user_tokens(project_name=project_name,site_name=site_name,user_id=user_id)
    notification_icon = data_dict.get("notification_icon") or ""

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

    response = messaging.send_each_for_multicast(message)
    return

def user_tokens(project_name,site_name,user_id):
    data=frappe.db.get_all(USER_TOKEN_DOCTYPE,
        filters={
            "project_name":project_name,
            "site_name":site_name,
            "user_id":user_id
        },
        fields=["fcm_token"])
    tokens = [item["fcm_token"] for item in data]
    return tokens
    


