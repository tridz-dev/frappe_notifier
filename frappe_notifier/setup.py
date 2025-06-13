import frappe
from frappe.core.doctype.user.user import generate_keys

def setup_users():
    try:
        # Create FN Notification Manager role if not exists
        if not frappe.db.exists("Role", "FN Notification Manager"):
            role = frappe.get_doc({
                "doctype": "Role",
                "role_name": "FN Notification Manager",
                "desk_access": 0
            })
            role.insert(ignore_permissions=True)
            frappe.db.commit()

        # Create Notification Manager user if not exists
        if not frappe.db.exists("User", "notification@site.com"):
            user = frappe.get_doc({
                "doctype": "User",
                "email": "notification@site.com",
                "first_name": "Notification",
                "last_name": "Manager",
                "enabled": 1,
                "user_type": "System User",
                "roles": [{"role": "FN Notification Manager"}]
            })
            user.insert(ignore_permissions=True)
            frappe.db.commit()
            
            # Generate API key and secret
            result = generate_keys("notification@site.com")
            api_secret = result.get("api_secret")
            user.reload()  # Reload to get the generated api_key
            api_key = user.api_key
            
            # Store credentials in Push Notification Settings
            if not frappe.db.exists("Push Notification Settings"):
                settings = frappe.get_doc({
                    "doctype": "Push Notification Settings",
                    "api_key": api_key,
                    "api_secret": api_secret
                })
                settings.insert(ignore_permissions=True)
            else:
                settings = frappe.get_doc("Push Notification Settings")
                settings.api_key = api_key
                settings.api_secret = api_secret
                settings.save(ignore_permissions=True)
                
            frappe.db.commit()
            frappe.msgprint("Notification Manager user created successfully with API credentials")
            print("Notification Manager user created successfully with API credentials")
        else:
            frappe.msgprint("Notification Manager user already exists")
            print("Notification Manager user already exists")
            
    except Exception as e:
        frappe.throw(str(e))
    