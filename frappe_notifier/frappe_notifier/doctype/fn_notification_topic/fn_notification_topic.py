# Copyright (c) 2025, Shahzad Bin Shahjahan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FNNotificationTopic(Document):
	pass

def get_channel_tokens_exclue_sender(channel_name:str,sender_id:str):
	topic_name = frappe.db.get_value("FN Notification Topic",{"topic_name":channel_name},"name")
	channel_users = frappe.db.get_all("FN Notification Topic User",
		filters={
			"parenttype":"FN Notification Topic",
			"parent":topic_name,
			"user_id":["!=",sender_id]
		},
		pluck="user_id"
	)
	if not channel_users:
		return []
	channel_tokens = frappe.db.get_all("FN User Device Token",
		filters={
			"user_id":["in",channel_users],
		},
		pluck="fcm_token"
	)
	if not channel_tokens:
		return []
	return channel_tokens