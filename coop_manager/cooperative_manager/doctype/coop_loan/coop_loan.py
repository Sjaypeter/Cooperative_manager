import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, date_diff, flt

MIN_RATIO = 0.50
MIN_MONTHS = 3

class CoopLoan(Document):
    def validate(self):
        if not self.loan_amount or self.loan_amount <= 0:
            frappe.throw("Loan amount must be greater than zero.")
        if not self.repayment_period_months or self.repayment_period_months <= 0:
            frappe.throw("Repayment period must be at least 1 month.")
        self.monthly_repayment = flt(self.loan_amount) / int(self.repayment_period_months)
        total_repaid = frappe.db.sql("""
            SELECT COALESCE(SUM(amount_paid),0) FROM `tabCoop Loan Repayment`
            WHERE loan=%s AND docstatus=1
        """, self.name)[0][0] or 0
        self.total_repaid = flt(total_repaid)
        self.outstanding_balance = flt(self.loan_amount) - self.total_repaid
        if self.outstanding_balance <= 0 and self.status == "Active":
            self.outstanding_balance = 0
            self.status = "Closed"

    def before_submit(self):
        if frappe.db.get_value("Coop Member", self.member, "status") != "Active":
            frappe.throw("Member must be Active to apply for a loan.")
        self._check_eligibility(throw=True)

    def on_submit(self):
        monthly = flt(self.loan_amount) / int(self.repayment_period_months)
        frappe.db.sql("""
            UPDATE `tabCoop Loan` 
            SET status='Approved', monthly_repayment=%s 
            WHERE name=%s
        """, (monthly, self.name))
        frappe.db.commit()

    def on_cancel(self):
        frappe.db.set_value("Coop Loan", self.name, "status", "Cancelled")

    def _check_eligibility(self, throw=False):
        contrib = frappe.db.sql("""
            SELECT COALESCE(SUM(amount),0) FROM `tabCoop Contribution`
            WHERE member=%s AND docstatus=1
        """, self.member)[0][0] or 0
        required = flt(self.loan_amount) * MIN_RATIO
        months = (date_diff(nowdate(),
            frappe.db.get_value("Coop Member", self.member, "date_joined")) or 0) // 30
        existing = frappe.db.count("Coop Loan",
            {"member": self.member, "status": "Active", "docstatus": 1,
             "name": ["!=", self.name]})
        r1 = flt(contrib) >= required
        r2 = months >= MIN_MONTHS
        r3 = existing == 0
        passed = r1 and r2 and r3
        msg = (f"{'ELIGIBLE' if passed else 'NOT ELIGIBLE'}\n"
               f"{'PASS' if r1 else 'FAIL'} Contributions: {contrib:,.0f} (need {required:,.0f})\n"
               f"{'PASS' if r2 else 'FAIL'} Membership: {months} months (need {MIN_MONTHS})\n"
               f"{'PASS' if r3 else 'FAIL'} No active loan: {'Yes' if r3 else 'No'}")
        if not passed and throw:
            frappe.throw(msg)
        return {"passed": passed, "message": msg}


@frappe.whitelist()
def check_eligibility(loan_name):
    loan = frappe.get_doc("Coop Loan", loan_name)
    result = loan._check_eligibility(throw=False)
    frappe.db.set_value("Coop Loan", loan_name, "eligibility_note", result["message"])
    return result["message"]


@frappe.whitelist()
def disburse(loan_name):
    frappe.db.set_value("Coop Loan", loan_name, {
        "status": "Active",
        "disbursement_date": nowdate()
    })
    return "Disbursed"


@frappe.whitelist()
def close_loan(loan_name):
    frappe.db.set_value("Coop Loan", loan_name, "status", "Closed")
    return "Closed"