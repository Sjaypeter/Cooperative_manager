import frappe

def execute(filters=None):
    filters = filters or {}
    member_condition = "AND m.name = %(member)s" if filters.get("member") else ""
    columns = [
        {"label": "Member ID", "fieldname": "member", "fieldtype": "Link",
         "options": "Coop Member", "width": 130},
        {"label": "Member Name", "fieldname": "member_name",
         "fieldtype": "Data", "width": 180},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 90},
        {"label": "Total Contributions", "fieldname": "total_contributions",
         "fieldtype": "Currency", "width": 160},
        {"label": "Total Loans Disbursed", "fieldname": "total_loans",
         "fieldtype": "Currency", "width": 170},
        {"label": "Total Repaid", "fieldname": "total_repayments",
         "fieldtype": "Currency", "width": 140},
        {"label": "Outstanding Balance", "fieldname": "outstanding_balance",
         "fieldtype": "Currency", "width": 160},
    ]
    data = frappe.db.sql(f"""
        SELECT m.name AS member, m.member_name, m.status,
            COALESCE((
                SELECT SUM(c.amount) FROM `tabCoop Contribution` c
                WHERE c.member=m.name AND c.docstatus=1
            ), 0) AS total_contributions,
            COALESCE((
                SELECT SUM(l.loan_amount) FROM `tabCoop Loan` l
                WHERE l.member=m.name AND l.docstatus=1
                AND l.status IN ('Active','Closed','Approved')
            ), 0) AS total_loans,
            COALESCE((
                SELECT SUM(r.amount_paid)
                FROM `tabCoop Loan Repayment` r
                INNER JOIN `tabCoop Loan` l ON r.loan=l.name
                WHERE l.member=m.name AND r.docstatus=1
            ), 0) AS total_repayments
        FROM `tabCoop Member` m
        WHERE m.docstatus != 2 {member_condition}
        ORDER BY m.member_name
    """, filters, as_dict=True)
    for row in data:
        row["outstanding_balance"] = max(
            (row["total_loans"] or 0) - (row["total_repayments"] or 0), 0)
    return columns, data
