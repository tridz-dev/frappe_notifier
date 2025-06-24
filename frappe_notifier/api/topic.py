import frappe
from firebase_admin import messaging
from frappe_notifier.api.send_notification import initialize_firebase_app
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
def remove(topic_name):
    """
    Removes a topic and unsubscribes all its users from Firebase.
    """
    try:
        initialize_firebase_app()
        topic_name=normalize_topic_name(topic_name)
        topic_doc_name = frappe.db.get_value("FN Notification Topic", {"topic_name": topic_name})

        if not topic_doc_name:
            return {"success": True, "message": "Topic not found."}

        # Get all subscribed user IDs for the topic
        topic_users = frappe.get_all("FN Notification Topic User", filters={"parent": topic_doc_name}, fields=["user_id"])
        user_ids = [user['user_id'] for user in topic_users]

        if user_ids:
            # Get all FCM tokens for these users
            all_tokens_data = frappe.get_all("FN User Device Token", filters={"user_id": ["in", user_ids]}, fields=["fcm_token"])
            all_tokens = [token['fcm_token'] for token in all_tokens_data if token.get('fcm_token')]

            # Unsubscribe all tokens from the Firebase topic in batches of 1000
            if all_tokens:
                for i in range(0, len(all_tokens), 1000):
                    batch = all_tokens[i:i+1000]
                    messaging.unsubscribe_from_topic(batch, topic_name)
        
        # Finally, delete the topic document from Frappe
        frappe.delete_doc("FN Notification Topic", topic_doc_name, ignore_permissions=True)
        return {"success": True, "message": f"Topic '{topic_name}' and all its subscribers have been removed."}
    except Exception as e:
        frappe.log_error(f"Failed to remove topic {topic_name}", str(e))
        raise e

@frappe.whitelist()
def subscribe(user_id, topic_name):
    """
    Subscribes a user's devices to a topic.
    """
    try:
        initialize_firebase_app()
        topic_name=normalize_topic_name(topic_name)
        add(topic_name) # Ensure topic exists
        # Check if user is already marked as subscribed in the database
        topic_doc_name = frappe.db.get_value("FN Notification Topic", {"topic_name": topic_name})
        if frappe.db.exists("FN Notification Topic User", {"parent": topic_doc_name, "user_id": user_id}):
            return {"success": True, "message": "User already subscribed to this topic."}

        # Get user's FCM tokens
        tokens = get_user_tokens(user_id)
        if not tokens:
            return {"success": False, "message": f"No device tokens found for user {user_id}."}

        # Subscribe tokens to the Firebase topic
        response = messaging.subscribe_to_topic(tokens, topic_name)
        if response.failure_count > 0:
            errors = [e.reason for e in response.errors]
            frappe.log_error(f"Partial failure subscribing to topic {topic_name} for user {user_id}: {errors}")
            # Proceed if at least one token was subscribed successfully
            if response.success_count == 0:
                raise Exception(f"Failed to subscribe any device to topic: {topic_name}. Errors: {errors}")
        
        # If subscription is successful, add user to the topic's child table
        add_user_to_topic(topic_doc_name, user_id)
        return {"success": True, "message": f"User {user_id} subscribed to topic {topic_name}."}

    except Exception as e:
        frappe.log_error(f"Subscription to topic {topic_name} for user {user_id} failed", str(e))
        raise e

@frappe.whitelist()
def unsubscribe(user_id, topic_name):
    """
    Unsubscribes a user's devices from a topic.
    """
    try:
        initialize_firebase_app()
        topic_name=normalize_topic_name(topic_name)

        topic_doc_name = frappe.db.get_value("FN Notification Topic", {"topic_name": topic_name})
        
        if not topic_doc_name or not frappe.db.exists("FN Notification Topic User", {"parent": topic_doc_name, "user_id": user_id}):
            return {"success": True, "message": "User is not subscribed to this topic."}

        tokens = get_user_tokens(user_id)
        if tokens:
            response = messaging.unsubscribe_from_topic(tokens, topic_name)
            if response.failure_count > 0:
                errors = [e.reason for e in response.errors]
                frappe.log_error(f"Partial failure unsubscribing from topic {topic_name} for user {user_id}: {errors}")
                if response.success_count == 0:
                    raise Exception(f"Failed to unsubscribe any device from topic: {topic_name}. Errors: {errors}")

        # Remove user from the topic's child table
        topic_user_doc = frappe.get_doc("FN Notification Topic User", {"parent": topic_doc_name, "user_id": user_id})
        frappe.delete_doc(topic_user_doc.doctype, topic_user_doc.name, ignore_permissions=True)
        return {"success": True, "message": f"User {user_id} unsubscribed from topic {topic_name}."}
        
    except Exception as e:
        frappe.log_error(f"Unsubscription from topic {topic_name} for user {user_id} failed", str(e))
        return e

def get_user_tokens(user_id: str) -> list[str]:
    """Helper function to get a user's FCM tokens."""
    tokens_data = frappe.db.get_all("FN User Device Token", filters={"user_id": user_id}, fields=["fcm_token"])
    return [item['fcm_token'] for item in tokens_data if item.get('fcm_token')]

def add_user_to_topic(topic_doc_name: str, user_id: str):
    """Helper function to add a user to a topic's child table."""
    child_doc = frappe.new_doc("FN Notification Topic User")
    child_doc.user_id = user_id
    child_doc.parent = topic_doc_name
    child_doc.parentfield = "user_ids"
    child_doc.parenttype = "FN Notification Topic"
    child_doc.insert(ignore_permissions=True)


