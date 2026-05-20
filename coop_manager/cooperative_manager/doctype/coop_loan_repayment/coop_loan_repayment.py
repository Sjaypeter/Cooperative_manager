import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate, flt

class CoopLoanRepayment(Document):
    def validate(self):
        loan_status = frappe.db.get_value("Coop Loan", self.loan, "status")
        if loan_status not in ("Active", "Approved"):
            frappe.throw("Repayments can only be posted to Active or Approved loans.")
        if flt(self.amount_paid) <= 0:
            frappe.throw("Amount must be greater than zero.")
        outstanding = flt(
            frappe.db.get_value("Coop Loan", self.loan, "outstanding_balance") or 0)
        if flt(self.amount_paid) > outstanding:
            frappe.throw(f"Amount exceeds outstanding balance of {outstanding:,.2f}.")
        disbursed = frappe.db.get_value("Coop Loan", self.loan, "disbursement_date")
        if disbursed and getdate(self.payment_date) < getdate(disbursed):
            frappe.throw("Payment date cannot be before disbursement date.")
        if getdate(self.payment_date) > getdate(nowdate()):
            frappe.throw("Payment date cannot be in the future.")

    def on_submit(self):
        frappe.get_doc("Coop Loan", self.loan).save(ignore_permissions=True)

    def on_cancel(self):
        frappe.get_doc("Coop Loan", self.loan).save(ignore_permissions=True)