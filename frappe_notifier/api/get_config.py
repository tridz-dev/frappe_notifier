import frappe
from werkzeug.wrappers import Response
import json

@frappe.whitelist(methods=["GET"],allow_guest=True)
def get_config():
    vapid_key=frappe.db.get_single_value("Frappe Notifier Settings","vapid_public_key");
    firebase_config=frappe.db.get_single_value("Frappe Notifier Settings","firebase_config");

    firebase_config_json=frappe.parse_json(firebase_config)

    data= {
        "vapid_public_key":vapid_key,
        "config":firebase_config_json
    }
    response = Response(json.dumps(data), content_type='application/json')
    response.status_code = 200
    return response