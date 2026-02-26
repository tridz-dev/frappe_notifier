import frappe

def extend_bootinfo(bootinfo):
    try:
        settings = frappe.get_single("Push Notification Settings")
        enabled = bool(getattr(settings, "enable_push_notification_relay", False))

        fcm_settings = frappe.get_single("Frappe Notifier Settings")
        firebase_config = fcm_settings.firebase_config
        vapid_public_key = fcm_settings.vapid_public_key
        if firebase_config:
            import json
            if isinstance(firebase_config, str):
                firebase_config = json.loads(firebase_config)

        bootinfo.frappe_notifier = {
            "firebase_config": firebase_config,
            "vapid_public_key": vapid_public_key,
            "push_notifications_enabled": enabled,
        }

    except Exception:
        frappe.log_error("Error loading push notification settings",frappe.get_traceback())