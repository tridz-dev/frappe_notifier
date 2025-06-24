import frappe
from frappe_notifier.utils.decorators import firebase_api_endpoint
from frappe_notifier.utils.firebase import subscribe_tokens_to_topic

@frappe.whitelist()
@firebase_api_endpoint
def add(project_name, site_name, user_id, fcm_token):
    if frappe.db.exists("FN User Device Token", {"user_id": user_id, "fcm_token": fcm_token}):
        return {"success": True, "message": "Token already exists."}

    token_doc = frappe.new_doc("FN User Device Token")
    token_doc.project_name = project_name
    token_doc.site_name = site_name
    token_doc.user_id = user_id
    token_doc.fcm_token = fcm_token
    token_doc.insert(ignore_permissions=True)
    
    check_topic_and_subscribe(user_id, fcm_token)
    return {"success": True, "message": "OK"}

@frappe.whitelist()
@firebase_api_endpoint
def remove(project_name, site_name, user_id, fcm_token):
    frappe.db.delete("FN User Device Token", {
        "fcm_token": fcm_token,
        "project_name": project_name,
        "site_name": site_name,
        "user_id": user_id
    })
    return {"success": True, "message": "Token removed."}

def check_topic_and_subscribe(user_id: str, fcm_token: str):
    """
    Checks if the user is already subscribed to topics and subscribes the new token to them.
    """
    subscribed_topics = frappe.get_all("FN Notification Topic User", {
        "user_id": user_id
    }, fields=["parent"])

    if not subscribed_topics:
        return

    topic_docs = frappe.get_all("FN Notification Topic", filters={
        "name": ("in", [d.parent for d in subscribed_topics])
    }, fields=["topic_name"])

    for topic in topic_docs:
        subscribe_tokens_to_topic([fcm_token], topic.topic_name)