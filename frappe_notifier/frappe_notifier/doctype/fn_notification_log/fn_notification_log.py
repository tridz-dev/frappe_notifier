# Copyright (c) 2025, Shahzad Bin Shahjahan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.query_builder import DocType
from frappe.query_builder.functions import Now
from frappe.utils import now_datetime, add_days
import json


class FNNotificationLog(Document):
	pass


def clear_old_logs():
	FN_LOG = DocType("FN Notification Log")

	# 14 days ago
	cutoff = add_days(now_datetime(), -14)
	# Use QB + frappe.db.delete
	frappe.db.delete(
		"FN Notification Log",
		filters={FN_LOG.modified: ("<", cutoff)}
	)