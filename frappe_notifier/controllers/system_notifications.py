import frappe
from frappe.utils import strip_html
from frappe_notifier.utils.firebase import initialize_firebase_app, get_user_tokens
from frappe_notifier.api.send_notification import send_notification

def on_insert(doc, method) -> None:
    frappe.enqueue(
        "frappe_notifier.controllers.system_notifications._send_push_for_notification_log",
        queue="short",
        notification_log_name=doc.name,
        now=frappe.flags.in_test,
    )


def _send_push_for_notification_log(notification_log_name: str) -> None:
    """Background job: load the Notification Log and send a push notification."""
    try:
        doc = frappe.get_doc("Notification Log", notification_log_name)
        if not getattr(doc, "for_user", None):
            return

        title = strip_html(doc.subject or "").strip() or "Notification"
        body = strip_html(doc.email_content or doc.subject or "").strip() or title

        initialize_firebase_app()
        tokens = get_user_tokens(
            project_name="grozfy",
            site_name=frappe.local.site,
            user_id=doc.for_user,
        )
        if not tokens:
            return

        send_notification(
            tokens=tokens,
            title=title,
            body=body,
            click_action=None,
            deactivate_invalid_tokens=True,
            extra_data={
                "document_type": str(doc.document_type or ""),
                "document_name": str(doc.document_name or ""),
                "notification_type": str(doc.type or ""),
                "notification_log_name": str(doc.name or ""),
                "click_action": "FLUTTER_NOTIFICATION_CLICK",
                "base_url": frappe.utils.get_url(),
            },
        )
    except Exception:
        frappe.log_error(
            f"Failed to send push notification for Notification Log {notification_log_name}"
        )
