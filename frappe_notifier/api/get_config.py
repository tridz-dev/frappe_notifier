import frappe
from werkzeug.wrappers import Response
import json

USER_TOKEN_DOCTYPE="Frappe Notifier Settings"
@frappe.whitelist(methods=["GET"],allow_guest=True)
def get_config():
    vapid_key=frappe.db.get_single_value(USER_TOKEN_DOCTYPE,"vapid_public_key");
    firebase_config_json=frappe.db.get_single_value(USER_TOKEN_DOCTYPE,"firebase_config");

    firebase_config=frappe.parse_json(firebase_config_json)

    data= {
        "vapid_public_key":vapid_key,
        "config":firebase_config
    }
    response = Response(json.dumps(data), content_type='application/json')
    response.status_code = 200
    return response