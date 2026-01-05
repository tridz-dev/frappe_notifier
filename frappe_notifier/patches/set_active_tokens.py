import frappe

def execute():
    if not frappe.db.has_column("FN User Device Token", "is_active"):
        return

    frappe.db.sql("""
        UPDATE `tabFN User Device Token`
        SET is_active = 1
    """)