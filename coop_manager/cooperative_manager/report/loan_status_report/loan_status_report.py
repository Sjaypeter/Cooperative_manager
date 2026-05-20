import frappe

def execute(filters=None):
    filters = filters or {}
    conditions = ["l.docstatus=1", "l.status NOT IN ('Cancelled', 'Draft')"]
    if filters.get("member"):
        conditions.append("l.member=%(member)s")
    if filters.get("status"):
        conditions.append("l.status=%(status)s")
    where = " AND ".join(conditions)
    columns = [
        {"label": "Loan ID", "fieldname": "loan_id", "fieldtype": "Link",
         "options": "Coop Loan", "width": 140},
        {"label": "Member", "fieldname": "member", "fieldtype": "Link",
         "options": "Coop Member", "width": 120},
        {"label": "Member Name", "fieldname": "member_name",
         "fieldtype": "Data", "width": 170},
        {"label": "Loan Amount", "fieldname": "loan_amount",
         "fieldtype": "Currency", "width": 130},
        {"label": "Monthly Repayment", "fieldname": "monthly_repayment",
         "fieldtype": "Currency", "width": 150},
        {"label": "Total Repaid", "fieldname": "total_repaid",
         "fieldtype": "Currency", "width": 130},
        {"label": "Outstanding", "fieldname": "outstanding_balance",
         "fieldtype": "Currency", "width": 150},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
    ]
    data = frappe.db.sql(f"""
        SELECT l.name AS loan_id, l.member, l.member_name,
               l.loan_amount, l.monthly_repayment, l.status,
               COALESCE(SUM(r.amount_paid), 0) AS total_repaid,
               (l.loan_amount - COALESCE(SUM(r.amount_paid), 0)) AS outstanding_balance
        FROM `tabCoop Loan` l
        LEFT JOIN `tabCoop Loan Repayment` r
            ON r.loan=l.name AND r.docstatus=1
        WHERE {where}
        GROUP BY l.name, l.member, l.member_name,
                 l.loan_amount, l.monthly_repayment, l.status
        ORDER BY l.creation DESC
    """, filters, as_dict=True)
    return columns, data