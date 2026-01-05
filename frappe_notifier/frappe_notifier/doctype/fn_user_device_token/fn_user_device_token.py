# Copyright (c) 2025, Shahzad Bin Shahjahan and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe
from frappe.query_builder import DocType


class FNUserDeviceToken(Document):
	pass

def deactivate_device_token(device_token: str):
    """
    Deactivates a device token in the database.
    """
    frappe.log_error(title="Deactivate device token", message=json.dumps({"device_token": device_token}, indent=2))
    frappe.db.set_value("FN User Device Token", {"fcm_token": device_token}, "is_active", 0)