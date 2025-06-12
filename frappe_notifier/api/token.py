import frappe

@frappe.whitelist()
def add(project_name,site_name,user_id,fcm_token):
    token_doc=frappe.new_doc("FN User Device Token")
    token_doc.project_name=project_name
    token_doc.site_name=site_name
    token_doc.user_id=user_id
    token_doc.fcm_token=fcm_token
    token_doc.insert()

@frappe.whitelist()
def remove(project_name,site_name,user_id,fcm_token):
    frappe.db.delete("FN User Device Token",{
        "fcm_token":fcm_token,
        "project_name":project_name,
        "site_name":site_name,
        "user_id":user_id
    });