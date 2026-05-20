import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, getdate, date_diff

class CoopMember(Document):
    def validate(self):
        if getdate(self.date_joined) > getdate(nowdate()):
            frappe.throw("Date Joined cannot be in the future.")

    def on_update(self):
        if self.has_value_changed("status") and self.status in ("Suspended", "Withdrawn"):
            for loan in frappe.get_all("Coop Loan",
                filters={"member": self.name, "status": "Draft", "docstatus": 0},
                pluck="name"):
                frappe.db.set_value("Coop Loan", loan, "status", "Cancelled")

@frappe.whitelist()
def get_member_summary(member_name):
    total = frappe.db.sql("""
        SELECT COALESCE(SUM(amount),0) FROM `tabCoop Contribution`
        WHERE member=%s AND docstatus=1
    """, member_name)[0][0] or 0
    active = frappe.db.count("Coop Loan",
        {"member": member_name, "status": "Active", "docstatus": 1})
    m = frappe.get_doc("Coop Member", member_name)
    months = (date_diff(nowdate(), m.date_joined) or 0) // 30
    return {"full_name": m.member_name, "status": m.status,
            "months_as_member": months, "total_contributions": total, "active_loans": active}
