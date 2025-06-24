import frappe
from firebase_admin import messaging
from frappe_notifier.utils.decorators import firebase_api_endpoint
from frappe_notifier.utils.firebase import get_user_tokens, subscribe_tokens_to_topic, unsubscribe_tokens_from_topic
from frappe_notifier.utils.normalize_topic_name import normalize_topic_name

@frappe.whitelist()
def add(topic_name):
    """
    Ensures a topic with the given name exists in the database.
    If it doesn't exist, it creates a new one.
    """
    topic_name=normalize_topic_name(topic_name)
    if not frappe.db.exists("FN Notification Topic", {"topic_name": topic_name}):
        topic = frappe.new_doc("FN Notification Topic")
        topic.topic_name = topic_name
        topic.insert()
    return {"success": True, "message": "OK"}

@frappe.whitelist()
@firebase_api_endpoint
def remove(topic_name):
    """
    Removes a topic and unsubscribes all its users from Firebase.
    """
    topic_name=normalize_topic_name(topic_name)
    topic_doc_name = frappe.db.get_value("FN Notification Topic", {"topic_name": topic_name})

    if not topic_doc_name:
        return {"success": True, "message": "Topic not found."}

    # Get all subscribed user IDs for the topic
    topic_users = frappe.get_all("FN Notification Topic User", filters={"parent": topic_doc_name}, fields=["user_id"])
    user_ids = [user['user_id'] for user in topic_users]

    if user_ids:
        all_tokens = get_user_tokens(user_id=user_ids)
        if all_tokens:
            # Unsubscribe all tokens from the Firebase topic in batches of 1000
            for i in range(0, len(all_tokens), 1000):
                batch = all_tokens[i:i+1000]
                unsubscribe_tokens_from_topic(batch, topic_name)
    
    frappe.delete_doc("FN Notification Topic", topic_doc_name, ignore_permissions=True)
    return {"success": True, "message": f"Topic '{topic_name}' and all its subscribers have been removed."}

@frappe.whitelist()
@firebase_api_endpoint
def subscribe(user_id, topic_name):
    """
    Subscribes a user's devices to a topic.
    """
    topic_name=normalize_topic_name(topic_name)
    add(topic_name) 

    topic_doc_name = frappe.db.get_value("FN Notification Topic", {"topic_name": topic_name})
    if frappe.db.exists("FN Notification Topic User", {"parent": topic_doc_name, "user_id": user_id}):
        frappe.log_error("------------user already exists")
        return {"success": True, "message": "User already subscribed to this topic."}

    tokens = get_user_tokens(user_id)
    if not tokens:
        return {"success": False, "message": f"No device tokens found for user {user_id}."}

    subscribe_tokens_to_topic(tokens, topic_name)
    
    add_user_to_topic(topic_doc_name, user_id)
    return {"success": True, "message": f"User {user_id} subscribed to topic {topic_name}."}

@frappe.whitelist()
@firebase_api_endpoint
def unsubscribe(user_id, topic_name):
    """
    Unsubscribes a user's devices from a topic.
    """
    topic_name=normalize_topic_name(topic_name)
    topic_doc_name = frappe.db.get_value("FN Notification Topic", {"topic_name": topic_name})
    
    if not topic_doc_name or not frappe.db.exists("FN Notification Topic User", {"parent": topic_doc_name, "user_id": user_id}):
        return {"success": True, "message": "User is not subscribed to this topic."}

    tokens = get_user_tokens(user_id)
    if tokens:
        unsubscribe_tokens_from_topic(tokens, topic_name)

    topic_user_doc = frappe.get_doc("FN Notification Topic User", {"parent": topic_doc_name, "user_id": user_id})
    frappe.delete_doc(topic_user_doc.doctype, topic_user_doc.name, ignore_permissions=True)
    return {"success": True, "message": f"User {user_id} unsubscribed from topic {topic_name}."}

def add_user_to_topic(topic_doc_name: str, user_id: str):
    """Helper function to add a user to a topic's child table."""
    child_doc = frappe.new_doc("FN Notification Topic User")
    child_doc.user_id = user_id
    child_doc.parent = topic_doc_name
    child_doc.parentfield = "user_ids"
    child_doc.parenttype = "FN Notification Topic"
    child_doc.insert(ignore_permissions=True)


