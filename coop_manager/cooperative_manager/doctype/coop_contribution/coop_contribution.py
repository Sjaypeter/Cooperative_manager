import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate

class CoopContribution(Document):
    def validate(self):
        if frappe.db.get_value("Coop Member", self.member, "status") != "Active":
            frappe.throw("Only Active members can make contributions.")
        if self.amount <= 0:
            frappe.throw("Amount must be greater than zero.")
        joined = frappe.db.get_value("Coop Member", self.member, "date_joined")
        if getdate(self.contribution_date) < getdate(joined):
            frappe.throw("Contribution date cannot be before member join date.")
        if getdate(self.contribution_date) > getdate(nowdate()):
            frappe.throw("Contribution date cannot be in the future.")

    def on_submit(self):
        self._update_member()

    def on_cancel(self):
        self._update_member()

    def _update_member(self):
        total = frappe.db.sql("""
            SELECT COALESCE(SUM(amount),0) FROM `tabCoop Contribution`
            WHERE member=%s AND docstatus=1
        """, self.member)[0][0] or 0
        frappe.db.set_value("Coop Member", self.member, "total_contributions", total)
