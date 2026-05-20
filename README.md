# Cooperative Manager — Frappe App

A lightweight Frappe application that covers the core operations of a cooperative society: member management, savings contributions, loan processing, and financial reporting.


---

## Table of Contents

- [Setup Instructions](#setup-instructions)
- [App Structure](#app-structure)
- [Features](#features)
- [Design Decisions & Assumptions](#design-decisions--assumptions)
- [Loan Eligibility Rule](#loan-eligibility-rule)
- [Known Issues & Limitations](#known-issues--limitations)
- [What I Would Add With More Time](#what-i-would-add-with-more-time)
- [Out of Scope](#out-of-scope)

---

## Setup Instructions

### Prerequisites

- Python 3.10+
- Node.js 18+
- Frappe Bench installed
- MariaDB running locally

### Installation

```bash
# 1. Create a new bench
bench init coop-bench --frappe-branch version-15
cd coop-bench

# 2. Create a new site
bench new-site coop.localhost --db-name coop_db

# 3. Get the app
bench get-app https://github.com/Sjaypeter/coop_manager

# 4. Install the app on the site
bench --site coop.localhost install-app coop_manager

# 5. Run migrations
bench --site coop.localhost migrate

# 6. Build assets
bench build --app coop_manager

# 7. Start the bench
bench start
```

### Access

Navigate to `http://coop.localhost:8000` and log in with your administrator credentials.

The app module is listed as **Cooperative Manager** in the Frappe desk.

---

## App Structure

```
coop_manager/
  cooperative_manager/
    doctype/
      coop_member/          # Member registration and management
      coop_contribution/    # Savings contribution records
      coop_loan/            # Loan applications and tracking
      coop_loan_repayment/  # Individual repayment entries
    report/
      member_statement_report/   # Per-member financial summary
      loan_status_report/        # All active loans across cooperative
```

---

## Features

### 1. Members (Coop Member)

- Register members with name, email, phone, address, and join date
- Status field: `Active`, `Suspended`, `Withdrawn`
- Auto-generated member ID (e.g. `COOP-0001`)
- `Total Contributions` computed field — updates automatically on contribution submit/cancel
- Status change to `Suspended` or `Withdrawn` automatically cancels any pending Draft loans for that member
- Validation: date joined cannot be in the future

### 2. Contributions (Coop Contribution)

- Record periodic savings contributions per member
- Submittable document — triggers balance update on the member record on submit and cancel
- Validations:
  - Only Active members can make contributions
  - Amount must be greater than zero
  - Contribution date cannot be before the member's join date
  - Contribution date cannot be in the future
- Payment mode tracked (Cash, Bank Transfer, etc.)

### 3. Loans (Coop Loan)

- Members apply for loans with a specified amount and repayment period
- `Monthly Repayment` is auto-calculated as `loan_amount / repayment_period_months`
- Loan lifecycle: `Draft → Approved → Active → Closed`
- `Total Repaid` and `Outstanding Balance` recalculate automatically whenever a repayment is submitted or cancelled
- Eligibility is checked at submission time — see [Loan Eligibility Rule](#loan-eligibility-rule)
- `check_eligibility` whitelisted method available to show a detailed eligibility breakdown
- `disburse` whitelisted method transitions status from `Approved → Active` and sets disbursement date
- `close_loan` whitelisted method for manual closure

### 4. Loan Repayments (Coop Loan Repayment)

- Each repayment is a submitted document linked to a specific loan
- Validations:
  - Loan must be Active or Approved
  - Amount must be greater than zero
  - Amount cannot exceed the current outstanding balance
  - Payment date cannot be before the loan disbursement date
  - Payment date cannot be in the future
- On submit/cancel, the parent loan recalculates its totals automatically

### 5. Reports

**Member Statement Report** (required)
- Shows all members with their total contributions, total loans disbursed, total repaid, and outstanding balance in a single view
- Filterable by individual member
  <img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/5571d97c-c31d-4e55-b2c1-6524e9bffe90" />


**Loan Status Report** (stretch goal — delivered)
- Shows all non-cancelled loans across the cooperative
- Columns: Loan ID, Member, Loan Amount, Monthly Repayment, Total Repaid, Outstanding Balance, Status
- Filterable by member and status
  <img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/478d8273-5b2a-4887-9b6a-a50ccf4efcf3" />


---

## Design Decisions & Assumptions

### Submittable Documents
Contributions and repayments are submittable (not just saved). This reflects how cooperative records should work — a submitted entry is a committed financial transaction that requires an explicit cancel action to reverse. This creates a clear audit trail.

### Loan Status as a Separate Field
Rather than relying solely on `docstatus`, I added an explicit `status` field to the loan (`Draft`, `Approved`, `Active`, `Closed`, `Cancelled`). This separates the Frappe submission state from the business workflow state, making it easier to add approval workflows later and giving the report layer a cleaner field to filter on.

### Total Contributions on Member Record
I stored `total_contributions` as a currency field on the member record and update it via a SQL aggregate on contribution submit/cancel. This is a deliberate denormalisation for read performance — report queries can read directly from the member record rather than summing contributions each time.

### Flat Repayment Model
As specified, repayments use a simple flat monthly figure with no interest or amortisation. The `monthly_repayment` field is informational — the system does not enforce that each repayment equals exactly the monthly amount. This allows partial payments and overpayments to be recorded, which matches how informal cooperative repayments often work in practice.

### Member Assumptions
- A member can only hold one Active loan at a time
- Suspended or Withdrawn members cannot take new loans (their Draft loans are auto-cancelled)
- Suspended members retain their contribution history — suspension is not the same as withdrawal

---

## Loan Eligibility Rule

A loan application is rejected at submission if any of the following conditions fail:

| Rule | Requirement | Reasoning |
|------|-------------|-----------|
| Contribution threshold | Total submitted contributions ≥ 50% of loan amount | A member must have demonstrated saving behaviour proportional to what they are borrowing. 50% was chosen as a reasonable middle ground — conservative enough to reduce default risk, not so strict that it blocks small emergency loans. |
| Minimum membership tenure | Member must have been active for at least 3 months | This prevents new members from immediately taking loans before the cooperative has any meaningful contribution history from them. |
| No concurrent active loans | Member must have no other Active loan | Prevents stacking of debt, which is a common risk control in cooperative lending. |

The eligibility check produces a detailed pass/fail breakdown visible to the administrator:

```
NOT ELIGIBLE
PASS Contributions: 40,000 (need 7,500)
FAIL Membership: 1 months (need 3)
PASS No active loan: Yes
```

These thresholds (`MIN_RATIO = 0.50`, `MIN_MONTHS = 3`) are defined as constants at the top of `coop_loan.py` and can be adjusted without touching logic.

---

## Known Issues & Limitations

### Disburse Button Not Rendering
A `coop_loan.js` client script adds a **Disburse Loan** button to the loan form when status is `Approved`. Due to a version-specific behaviour in this Frappe installation where `frm.add_custom_button` with a group name collapses into the `...` overflow menu rather than rendering as a standalone button, the button is not immediately visible.

**Workaround used during development:**
```python
# bench --site coop.localhost console
from frappe.utils import nowdate
frappe.db.set_value("Coop Loan", "LOAN-XXXXX", {"status": "Active", "disbursement_date": nowdate()})
frappe.db.commit()
```

**Production fix:** Implement a proper Frappe Workflow on the Coop Loan doctype with defined states and transition actions — this is the idiomatic Frappe way to handle multi-step status transitions with UI buttons.

### Monthly Repayment on Existing Submitted Loans
The `monthly_repayment` field is calculated in `validate()` which does not fire again after submission. Loans submitted before this calculation was added show NGN 0.00. Fixed going forward via the `on_submit` SQL update. Existing records can be corrected via console or a migration script.

### Negative Outstanding Balances in Test Data
Some earlier test loans show negative outstanding balances caused by repayments posted for amounts exceeding the loan value during development. In production, the repayment validation (`amount_paid > outstanding_balance` check) prevents this. The affected records are test data only.

---

## What I Would Add With More Time

**Frappe Workflow for loan lifecycle**
Replace the manual status transitions with a proper Frappe Workflow — this would give proper UI buttons, role-based transition permissions, and an audit trail of who approved and disbursed each loan.

**Member portal / self-service**
A simple web view where members can check their own contribution history and loan status without needing desk access.

**Repayment schedule**
Auto-generate expected repayment dates when a loan is disbursed, so administrators can see which repayments are upcoming, on time, or overdue.

**Delinquency tracking**
Flag loans where repayments are overdue based on disbursement date and expected monthly schedule.

**Multiple branches**
Add a `Branch` doctype and link members and loans to branches. Reports would gain a branch filter. Members could be shared across branches with branch-specific loan limits.

**Notifications**
Email or SMS reminders for upcoming repayment due dates.

**Audit log improvements**
Track who approved and disbursed each loan, with timestamps.

---



## Tech Stack

- **Framework:** Frappe v15
- **Language:** Python 3.12
- **Database:** MariaDB
- **Frontend:** Frappe Desk (standard)

---

*Built by Peter Saint-john — May 2026*
