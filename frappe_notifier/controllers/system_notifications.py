import frappe
from frappe.utils import get_url_to_form, strip_html

def on_insert(doc, method) -> None:
    frappe.enqueue(
        "frappe_notifier.controllers.system_notifications._send_push_for_notification_log",
        queue="short",
        notification_log_name=doc.name,
        now=frappe.flags.in_test,
        enqueue_after_commit=True,
    )


def _send_push_for_notification_log(notification_log_name: str) -> None:
    """Background job: load the Notification Log and send a push notification."""
    try:
        doc = frappe.get_doc("Notification Log", notification_log_name)
        if not getattr(doc, "for_user", None):
            return

        # Title: concise, plain‑text subject
        raw_title = doc.subject or ""
        title = strip_html(raw_title).strip() or "Notification"

        # Message/body: prefer email_content, fallback to subject
        raw_body = doc.email_content or doc.subject or ""
        message = strip_html(raw_body).strip() or title

        # Link: explicit link on the log, or fall back to the target document
        if doc.link:
            link = doc.link
        elif doc.document_type and doc.document_name:
            link = get_url_to_form(doc.document_type, doc.document_name)
        else:
            link = None

        # Extra context for the client
        data = {
            "notification_log_name": doc.name,
            "notification_type": doc.type,
            "document_type": doc.document_type,
            "document_name": doc.document_name,
        }

        send_notification_to_user(
            user_id=doc.for_user,
            title=title,
            message=message,
            link=link,
            data=data,
        )
    except Exception:
        frappe.log_error(
            f"Failed to send push notification for Notification Log {notification_log_name}"
        )


def send_notification_to_user(
    user_id: str,
    title: str,
    message: str,
    link: str | None = None,
    data: dict | None = None,
) -> None:
    """Send a push notification to a single Frappe user via the Push Notification Relay."""

    try:
        from frappe.push_notification import PushNotification

        # Project name must match what you used when registering tokens.
        push_notification = PushNotification("frappe_desk")

        payload = dict(data or {})
        payload.setdefault("base_url", frappe.utils.get_url())
        payload.setdefault("sitename", frappe.local.site)

        if not push_notification.is_enabled():
            return

        icon_url = None
        push_notification.send_notification_to_user(
            user_id=user_id,
            title=title,
            body=message,
            icon=icon_url,
            data=payload,
            link=link,
        )
    except ImportError:
        # Push notifications are not available on this Frappe version.
        return
    except Exception:
        frappe.log_error("Failed to send push notification")
