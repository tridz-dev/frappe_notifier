import frappe
from functools import wraps
from frappe_notifier.utils.firebase import initialize_firebase_app

def firebase_api_endpoint(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            initialize_firebase_app()
            return f(*args, **kwargs)
        except Exception as e:
            frappe.log_error(title=f"Firebase API Error in {f.__name__}", message=str(e))
            # Use frappe.get_response to ensure a proper HTTP response is sent
            raise e
    return wrapper 