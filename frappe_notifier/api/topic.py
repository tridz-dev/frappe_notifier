import frappe

@frappe.whitelist(allow_guest=True)
def add(topic_name):
    topic_exists=frappe.db.exists("FN Notification Topic",{
        "topic_name":topic_name
    })
    if topic_exists:
        return {"success": True, "message": "OK"}
    topic=frappe.new_doc("FN Notification Topic")
    topic.topic_name=topic_name
    topic.insert()
    return {"success": True, "message": "OK"}

@frappe.whitelist(allow_guest=True)
def remove(topic_name):
    topic_exists=frappe.db.exists("FN Notification Topic",{
        "topic_name":topic_name
    })
    if not topic_exists:
        return {"success": True, "message": "OKk"}
    topic_id=frappe.db.get_value("FN Notification Topic",{
        "topic_name":topic_name
    },"name")
    frappe.delete_doc("FN Notification Topic",topic_id)
    return {"success": True, "message": "OK bro"}