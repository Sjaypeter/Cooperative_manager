// Copyright (c) 2026, Peter Saint-john and contributors
// For license information, please see license.txt

frappe.ui.form.on('Coop Loan', {
    refresh(frm) {
        // Show Disburse button when loan is Approved and submitted
        if (frm.doc.status === 'Approved' && frm.doc.docstatus === 1) {
            frm.add_custom_button('Disburse Loan', function () {
                frappe.confirm(
                    'Are you sure you want to disburse this loan?',
                    function () {
                        frappe.call({
                            method: 'cooperative_manager.cooperative_manager.doctype.coop_loan.coop_loan.disburse',
                            args: { loan_name: frm.doc.name },
                            callback: function (r) {
                                if (!r.exc) {
                                    frappe.msgprint('Loan disbursed successfully.');
                                    frm.reload_doc();
                                }
                            }
                        });
                    }
                );
            });
        }

        // Show Check Eligibility button on Active loans
        if (frm.doc.status === 'Active' && frm.doc.docstatus === 1) {
            frm.add_custom_button('Check Eligibility', function () {
                frappe.call({
                    method: 'cooperative_manager.cooperative_manager.doctype.coop_loan.coop_loan.check_eligibility',
                    args: { loan_name: frm.doc.name },
                    callback: function (r) {
                        if (r.message) {
                            frappe.msgprint({
                                title: 'Eligibility Result',
                                message: r.message.replace(/\n/g, '<br>'),
                                indicator: r.message.includes('ELIGIBLE') ? 'green' : 'red'
                            });
                        }
                    }
                });
            });
        }

        // Show Close Loan button on Active loans
        if (frm.doc.status === 'Active' && frm.doc.docstatus === 1) {
            frm.add_custom_button('Close Loan', function () {
                frappe.confirm(
                    'Mark this loan as Closed?',
                    function () {
                        frappe.call({
                            method: 'cooperative_manager.cooperative_manager.doctype.coop_loan.coop_loan.close_loan',
                            args: { loan_name: frm.doc.name },
                            callback: function (r) {
                                if (!r.exc) {
                                    frappe.msgprint('Loan closed.');
                                    frm.reload_doc();
                                }
                            }
                        });
                    }
                );
            });
        }
    }
});