# # -*- coding: utf-8 -*-
# # Copyright (c) 2020, Youssef Restom and contributors
# # For license information, please see license.txt

# from __future__ import unicode_literals
# import frappe
# import json
# from frappe import _
# from frappe.model.document import Document
# from frappe.utils import flt


# class POSClosingShift(Document):
#     def validate(self):
#         user = frappe.get_all(
#             "POS Closing Shift",
#             filters={
#                 "user": self.user,
#                 "docstatus": 1,
#                 "pos_opening_shift": self.pos_opening_shift,
#                 "name": ["!=", self.name],
#             },
#         )

#         if user:
#             frappe.throw(
#                 _(
#                     "POS Closing Shift {} against {} between selected period".format(
#                         frappe.bold("already exists"), frappe.bold(self.user)
#                     )
#                 ),
#                 title=_("Invalid Period"),
#             )

#         if (
#             frappe.db.get_value("POS Opening Shift", self.pos_opening_shift, "status")
#             != "Open"
#         ):
#             frappe.throw(
#                 _("Selected POS Opening Shift should be open."),
#                 title=_("Invalid Opening Entry"),
#             )
#         self.update_payment_reconciliation()

#     def update_payment_reconciliation(self):
#         # update the difference values in Payment Reconciliation child table
#         # get default precision for site
#         precision = (
#             frappe.get_cached_value("System Settings", None, "currency_precision") or 3
#         )
#         for d in self.payment_reconciliation:
#             d.difference = +flt(d.closing_amount, precision) - flt(
#                 d.expected_amount, precision
#             )

#     def on_submit(self):
#         opening_entry = frappe.get_doc("POS Opening Shift", self.pos_opening_shift)
#         opening_entry.pos_closing_shift = self.name
#         opening_entry.set_status()
#         self.delete_draft_invoices()
#         opening_entry.save()

#     def on_cancel(self):
#         if frappe.db.exists("POS Opening Shift", self.pos_opening_shift):
#             opening_entry = frappe.get_doc("POS Opening Shift", self.pos_opening_shift)
#             if opening_entry.pos_closing_shift == self.name:
#                 opening_entry.pos_closing_shift = ""
#                 opening_entry.set_status()
#                 opening_entry.save()

#     def delete_draft_invoices(self):
#         if frappe.get_value("POS Profile", self.pos_profile, "posa_allow_delete"):
#             data = frappe.db.sql(
#                 """
#                 select
#                     name
#                 from
#                     `tabSales Invoice`
#                 where
#                     docstatus = 0 and posa_is_printed = 0 and posa_pos_opening_shift = %s
#                 """,
#                 (self.pos_opening_shift),
#                 as_dict=1,
#             )

#             for invoice in data:
#                 frappe.delete_doc("Sales Invoice", invoice.name, force=1)

#     @frappe.whitelist()
#     def get_payment_reconciliation_details(self):
#         currency = frappe.get_cached_value("Company", self.company, "default_currency")
#         return frappe.render_template(
#             "posawesome/posawesome/doctype/pos_closing_shift/closing_shift_details.html",
#             {"data": self, "currency": currency},
#         )


# @frappe.whitelist()
# def get_cashiers(doctype, txt, searchfield, start, page_len, filters):
#     cashiers_list = frappe.get_all("POS Profile User", filters=filters, fields=["user"])
#     result = []
#     for cashier in cashiers_list:
#         user_email = frappe.get_value("User", cashier.user, "email")
#         if user_email:
#             # Return list of tuples in format (value, label) where value is user ID and label shows both ID and email
#             result.append([cashier.user, f"{cashier.user} ({user_email})"])
#     return result


# @frappe.whitelist()
# def get_pos_invoices(pos_opening_shift):
#     submit_printed_invoices(pos_opening_shift)
#     data = frappe.db.sql(
#         """
# 	select
# 		name
# 	from
# 		`tabSales Invoice`
# 	where
# 		docstatus = 1 and posa_pos_opening_shift = %s
# 	""",
#         (pos_opening_shift),
#         as_dict=1,
#     )

#     data = [frappe.get_doc("Sales Invoice", d.name).as_dict() for d in data]

#     return data


# @frappe.whitelist()
# def get_payments_entries(pos_opening_shift):
#     return frappe.get_all(
#         "Payment Entry",
#         filters={
#             "docstatus": 1,
#             "reference_no": pos_opening_shift,
#             "payment_type": "Receive",
#         },
#         fields=[
#             "name",
#             "mode_of_payment",
#             "paid_amount",
#             "reference_no",
#             "posting_date",
#             "party",
#         ],
#     )


# @frappe.whitelist()
# def make_closing_shift_from_opening(opening_shift):
#     opening_shift = json.loads(opening_shift)
#     submit_printed_invoices(opening_shift.get("name"))
#     closing_shift = frappe.new_doc("POS Closing Shift")
#     closing_shift.pos_opening_shift = opening_shift.get("name")
#     closing_shift.period_start_date = opening_shift.get("period_start_date")
#     closing_shift.period_end_date = frappe.utils.get_datetime()
#     closing_shift.pos_profile = opening_shift.get("pos_profile")
#     closing_shift.user = opening_shift.get("user")
#     closing_shift.company = opening_shift.get("company")
#     closing_shift.grand_total = 0
#     closing_shift.net_total = 0
#     closing_shift.total_quantity = 0

#     invoices = get_pos_invoices(opening_shift.get("name"))

#     pos_transactions = []
#     taxes = []
#     payments = []
#     pos_payments_table = []
#     for detail in opening_shift.get("balance_details"):
#         payments.append(
#             frappe._dict(
#                 {
#                     "mode_of_payment": detail.get("mode_of_payment"),
#                     "opening_amount": detail.get("amount") or 0,
#                     "expected_amount": detail.get("amount") or 0,
#                 }
#             )
#         )

#     for d in invoices:
#         pos_transactions.append(
#             frappe._dict(
#                 {
#                     "sales_invoice": d.name,
#                     "posting_date": d.posting_date,
#                     "grand_total": d.grand_total,
#                     "customer": d.customer,
#                 }
#             )
#         )
#         closing_shift.grand_total += flt(d.grand_total)
#         closing_shift.net_total += flt(d.net_total)
#         closing_shift.total_quantity += flt(d.total_qty)

#         for t in d.taxes:
#             existing_tax = [
#                 tx
#                 for tx in taxes
#                 if tx.account_head == t.account_head and tx.rate == t.rate
#             ]
#             if existing_tax:
#                 existing_tax[0].amount += flt(t.tax_amount)
#             else:
#                 taxes.append(
#                     frappe._dict(
#                         {
#                             "account_head": t.account_head,
#                             "rate": t.rate,
#                             "amount": t.tax_amount,
#                         }
#                     )
#                 )

#         for p in d.payments:
#             existing_pay = [
#                 pay for pay in payments if pay.mode_of_payment == p.mode_of_payment
#             ]
#             if existing_pay:
#                 cash_mode_of_payment = frappe.get_value(
#                     "POS Profile",
#                     opening_shift.get("pos_profile"),
#                     "posa_cash_mode_of_payment",
#                 )
#                 if not cash_mode_of_payment:
#                     cash_mode_of_payment = "Cash"
#                 if existing_pay[0].mode_of_payment == cash_mode_of_payment:
#                     amount = p.amount - d.change_amount
#                 else:
#                     amount = p.amount
#                 existing_pay[0].expected_amount += flt(amount)
#             else:
#                 payments.append(
#                     frappe._dict(
#                         {
#                             "mode_of_payment": p.mode_of_payment,
#                             "opening_amount": 0,
#                             "expected_amount": p.amount,
#                         }
#                     )
#                 )

#     pos_payments = get_payments_entries(opening_shift.get("name"))

#     for py in pos_payments:
#         pos_payments_table.append(
#             frappe._dict(
#                 {
#                     "payment_entry": py.name,
#                     "mode_of_payment": py.mode_of_payment,
#                     "paid_amount": py.paid_amount,
#                     "posting_date": py.posting_date,
#                     "customer": py.party,
#                 }
#             )
#         )
#         existing_pay = [
#             pay for pay in payments if pay.mode_of_payment == py.mode_of_payment
#         ]
#         if existing_pay:
#             existing_pay[0].expected_amount += flt(py.paid_amount)
#         else:
#             payments.append(
#                 frappe._dict(
#                     {
#                         "mode_of_payment": py.mode_of_payment,
#                         "opening_amount": 0,
#                         "expected_amount": py.paid_amount,
#                     }
#                 )
#             )

#     closing_shift.set("pos_transactions", pos_transactions)
#     closing_shift.set("payment_reconciliation", payments)
#     closing_shift.set("taxes", taxes)
#     closing_shift.set("pos_payments", pos_payments_table)

#     return closing_shift


# @frappe.whitelist()
# def submit_closing_shift(closing_shift):
#     closing_shift = json.loads(closing_shift)
#     closing_shift_doc = frappe.get_doc(closing_shift)
#     closing_shift_doc.flags.ignore_permissions = True
#     closing_shift_doc.save()
#     closing_shift_doc.submit()
#     return closing_shift_doc.name


# def submit_printed_invoices(pos_opening_shift):
#     invoices_list = frappe.get_all(
#         "Sales Invoice",
#         filters={
#             "posa_pos_opening_shift": pos_opening_shift,
#             "docstatus": 0,
#             "posa_is_printed": 1,
#         },
#     )
#     for invoice in invoices_list:
#         invoice_doc = frappe.get_doc("Sales Invoice", invoice.name)
#         invoice_doc.submit()


# -*- coding: utf-8 -*-
# Copyright (c) 2020, Youssef Restom and contributors
# For license information, please see license.txt

# -*- coding: utf-8 -*-
# Copyright (c) 2020, Youssef Restom and contributors
# For license information, please see license.txt

# -*- coding: utf-8 -*-
# Copyright (c) 2020, Youssef Restom and contributors
# For license information, please see license.txt

# -*- coding: utf-8 -*-
# Copyright (c) 2020, Youssef Restom and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import _
from frappe.model.document import Document
from erpnext.accounts.party import get_party_account
from erpnext.controllers.accounts_controller import AccountsController
from frappe.utils import flt
try:
    from erpnext.accounts.general_ledger import make_gl_entries
except ImportError:
    # Fallback if make_gl_entries is not available
    make_gl_entries = None


class POSClosingShift(AccountsController):
    def validate(self):
        user = frappe.get_all(
            "POS Closing Shift",
            filters={
                "user": self.user,
                "docstatus": 1,
                "pos_opening_shift": self.pos_opening_shift,
                "name": ["!=", self.name],
            },
        )

        if user:
            frappe.throw(
                _(
                    "POS Closing Shift {} against {} between selected period".format(
                        frappe.bold("already exists"), frappe.bold(self.user)
                    )
                ),
                title=_("Invalid Period"),
            )

        if (
            frappe.db.get_value("POS Opening Shift", self.pos_opening_shift, "status")
            != "Open"
        ):
            frappe.throw(
                _("Selected POS Opening Shift should be open."),
                title=_("Invalid Opening Entry"),
            )

        # Validate custom accounts from POS Profile
        pos_profile = frappe.get_doc("POS Profile", self.pos_profile)
        if pos_profile.custom_cash_shortage and not frappe.db.exists("Account", pos_profile.custom_cash_shortage):
            frappe.throw(_("Invalid Cash Shortage Account: {}").format(pos_profile.custom_cash_shortage))
        if pos_profile.custom_cash_excess and not frappe.db.exists("Account", pos_profile.custom_cash_excess):
            frappe.throw(_("Invalid Cash Excess Account: {}").format(pos_profile.custom_cash_excess))

        self.update_payment_reconciliation()

    def update_payment_reconciliation(self):
        # Update the difference values in Payment Reconciliation child table
        precision = (
            frappe.get_cached_value("System Settings", None, "currency_precision") or 3
        )
        for d in self.payment_reconciliation:
            d.difference = flt(d.closing_amount, precision) - flt(
                d.expected_amount, precision
            )

    def on_submit(self):
        opening_entry = frappe.get_doc("POS Opening Shift", self.pos_opening_shift)
        opening_entry.pos_closing_shift = self.name
        opening_entry.set_status()
        self.delete_draft_invoices()
        opening_entry.save()
        pos_profile = frappe.get_doc("POS Profile", self.pos_profile)
        if pos_profile.custom__enable_gl_impact_on_shift_closing:
            self.make_gl_entries_for_cash_differences()

    def on_cancel(self):
        if frappe.db.exists("POS Opening Shift", self.pos_opening_shift):
            opening_entry = frappe.get_doc("POS Opening Shift", self.pos_opening_shift)
            if opening_entry.pos_closing_shift == self.name:
                opening_entry.pos_closing_shift = ""
                opening_entry.set_status()
                opening_entry.save()
        self.reverse_gl_entries_for_cash_differences()

    def delete_draft_invoices(self):
        if frappe.get_value("POS Profile", self.pos_profile, "posa_allow_delete"):
            data = frappe.db.sql(
                """
                select
                    name
                from
                    `tabSales Invoice`
                where
                    docstatus = 0 and posa_is_printed = 0 and posa_pos_opening_shift = %s
                """,
                (self.pos_opening_shift),
                as_dict=1,
            )

            for invoice in data:
                frappe.delete_doc("Sales Invoice", invoice.name, force=1)
    
    # def get_cash_account(self):
    #     # Get the default account for the cash mode of payment from Mode of Payment accounts
    #     cash_mode_of_payment = frappe.get_value(
    #         "POS Profile", self.pos_profile, "posa_cash_mode_of_payment"
    #     ) or "Cash"
    #     account = frappe.get_value(
    #         "Mode of Payment Account",
    #         {"parent": cash_mode_of_payment, "company": self.company},
    #         "default_account"
    #     )
    #     if not account:
    #         frappe.throw(
    #             _("No default account set for Mode of Payment {0} in company {1}").format(
    #                 frappe.bold(cash_mode_of_payment), frappe.bold(self.company)
    #             )
    #         )
    #     return account

    def get_cash_account(self):
        cash_mode_of_payment = frappe.get_value("POS Profile", self.pos_profile, "posa_cash_mode_of_payment") or "Cash"
        account = frappe.get_value(
            "Mode of Payment Account",
            {"parent": cash_mode_of_payment, "company": self.company},
            "default_account"
        )
        frappe.log_error(f"Cash Mode: {cash_mode_of_payment}, Account: {account}", "Debug Cash Account")
        if not account:
            frappe.throw(
                _("No default account set for Mode of Payment {0} in company {1}").format(
                    frappe.bold(cash_mode_of_payment), frappe.bold(self.company)
                )
            )
        return account

    def make_gl_entries_for_cash_differences(self):
        # Create GL entries for cash shortages or excesses
        cash_mode_of_payment = frappe.get_value(
            "POS Profile", self.pos_profile, "posa_cash_mode_of_payment"
        ) or "Cash"
        cash_payment = next(
            (p for p in self.payment_reconciliation if p.mode_of_payment == cash_mode_of_payment),
            None,
        )

        if not cash_payment or not cash_payment.difference:
            return

        company = self.company
        posting_date = self.posting_date
        cash_account = self.get_cash_account()
        pos_profile = frappe.get_doc("POS Profile", self.pos_profile)
        shortage_account = pos_profile.custom_cash_shortage
        excess_account = pos_profile.custom_cash_excess
        cost_center = pos_profile.write_off_cost_center or frappe.get_cached_value("Company", company, "default_cost_center")

        if not cash_account:
            frappe.throw(_("Cash account not found for Mode of Payment {0} in company {1}.").format(
                frappe.bold(cash_mode_of_payment), frappe.bold(company)
            ))
        if not cost_center:
            frappe.throw(_("Cost center is required. Please set write_off_cost_center in POS Profile or default_cost_center in Company."))

        gl_entries = []
        if cash_payment.difference > 0:
            if not excess_account:
                frappe.throw(_("Cash Excess Account is not set in POS Profile."))
            gl_entries.append(
                self.get_gl_dict(
                    {
                        "account": cash_account,
                        "debit": cash_payment.difference,
                        "debit_in_account_currency": cash_payment.difference,
                        "against": excess_account,
                        "posting_date": posting_date,
                        "company": company,
                        "cost_center": cost_center,
                        "remarks": "Cash excess from POS Closing Shift",
                    },
                    item=self,
                )
            )
            gl_entries.append(
                self.get_gl_dict(
                    {
                        "account": excess_account,
                        "credit": cash_payment.difference,
                        "credit_in_account_currency": cash_payment.difference,
                        "against": cash_account,
                        "posting_date": posting_date,
                        "company": company,
                        "cost_center": cost_center,
                        "remarks": "Cash excess from POS Closing Shift",
                    },
                    item=self,
                )
            )
        elif cash_payment.difference < 0:
            if not shortage_account:
                frappe.throw(_("Cash Shortage Account is not set in POS Profile."))
            gl_entries.append(
                self.get_gl_dict(
                    {
                        "account": shortage_account,
                        "debit": abs(cash_payment.difference),
                        "debit_in_account_currency": abs(cash_payment.difference),
                        "against": cash_account,
                        "posting_date": posting_date,
                        "company": company,
                        "cost_center": cost_center,
                        "remarks": "Cash shortage from POS Closing Shift",
                    },
                    item=self,
                )
            )
            gl_entries.append(
                self.get_gl_dict(
                    {
                        "account": cash_account,
                        "credit": abs(cash_payment.difference),
                        "credit_in_account_currency": abs(cash_payment.difference),
                        "against": shortage_account,
                        "posting_date": posting_date,
                        "company": company,
                        "cost_center": cost_center,
                        "remarks": "Cash shortage from POS Closing Shift",
                    },
                    item=self,
                )
            )

        if gl_entries:
            frappe.log_error(f"Creating GL entries for POS Closing Shift {self.name}", "POS Closing Shift")
            if make_gl_entries:
                make_gl_entries(gl_entries, cancel=False, merge_entries=True)
            else:
                for entry in gl_entries:
                    gl_entry = frappe.get_doc({
                        "doctype": "GL Entry",
                        "posting_date": entry.get("posting_date"),
                        "account": entry.get("account"),
                        "debit": entry.get("debit", 0),
                        "credit": entry.get("credit", 0),
                        "debit_in_account_currency": entry.get("debit_in_account_currency", 0),
                        "credit_in_account_currency": entry.get("credit_in_account_currency", 0),
                        "against": entry.get("against"),
                        "voucher_type": "POS Closing Shift",
                        "voucher_no": self.name,
                        "company": entry.get("company"),
                        "cost_center": entry.get("cost_center"),
                        "remarks": entry.get("remarks"),
                    })
                    gl_entry.insert(ignore_permissions=True)

    def reverse_gl_entries_for_cash_differences(self):
        cash_mode_of_payment = frappe.get_value(
            "POS Profile", self.pos_profile, "posa_cash_mode_of_payment"
        ) or "Cash"
        cash_payment = next(
            (p for p in self.payment_reconciliation if p.mode_of_payment == cash_mode_of_payment),
            None,
        )

        if not cash_payment or not cash_payment.difference:
            return

        company = self.company
        posting_date = self.posting_date
        cash_account = self.get_cash_account()
        pos_profile = frappe.get_doc("POS Profile", self.pos_profile)
        shortage_account = pos_profile.custom_cash_shortage
        excess_account = pos_profile.custom_cash_excess
        cost_center = pos_profile.write_off_cost_center or frappe.get_cached_value("Company", company, "default_cost_center")

        if not cash_account:
            frappe.throw(_("Cash account not found for Mode of Payment {0} in company {1}.").format(
                frappe.bold(cash_mode_of_payment), frappe.bold(company)
            ))
        if not cost_center:
            frappe.throw(_("Cost center is required. Please set write_off_cost_center in POS Profile or default_cost_center in Company."))

        gl_entries = []
        if cash_payment.difference > 0:
            if not excess_account:
                frappe.throw(_("Cash Excess Account is not set in POS Profile."))
            gl_entries.append(
                self.get_gl_dict(
                    {
                        "account": cash_account,
                        "credit": cash_payment.difference,
                        "credit_in_account_currency": cash_payment.difference,
                        "against": excess_account,
                        "posting_date": posting_date,
                        "company": company,
                        "cost_center": cost_center,
                        "remarks": "Reversal of cash excess from POS Closing Shift cancellation",
                    },
                    item=self,
                )
            )
            gl_entries.append(
                self.get_gl_dict(
                    {
                        "account": excess_account,
                        "debit": cash_payment.difference,
                        "debit_in_account_currency": cash_payment.difference,
                        "against": cash_account,
                        "posting_date": posting_date,
                        "company": company,
                        "cost_center": cost_center,
                        "remarks": "Reversal of cash excess from POS Closing Shift cancellation",
                    },
                    item=self,
                )
            )
        elif cash_payment.difference < 0:
            if not shortage_account:
                frappe.throw(_("Cash Shortage Account is not set in POS Profile."))
            gl_entries.append(
                self.get_gl_dict(
                    {
                        "account": shortage_account,
                        "credit": abs(cash_payment.difference),
                        "credit_in_account_currency": abs(cash_payment.difference),
                        "against": cash_account,
                        "posting_date": posting_date,
                        "company": company,
                        "cost_center": cost_center,
                        "remarks": "Reversal of cash shortage from POS Closing Shift cancellation",
                    },
                    item=self,
                )
            )
            gl_entries.append(
                self.get_gl_dict(
                    {
                        "account": cash_account,
                        "debit": abs(cash_payment.difference),
                        "debit_in_account_currency": abs(cash_payment.difference),
                        "against": shortage_account,
                        "posting_date": posting_date,
                        "company": company,
                        "cost_center": cost_center,
                        "remarks": "Reversal of cash shortage from POS Closing Shift cancellation",
                    },
                    item=self,
                )
            )

        if gl_entries:
            frappe.log_error(f"Reversing GL entries for POS Closing Shift {self.name}", "POS Closing Shift")
            if make_gl_entries:
                make_gl_entries(gl_entries, cancel=False, merge_entries=True)
            else:
                for entry in gl_entries:
                    gl_entry = frappe.get_doc({
                        "doctype": "GL Entry",
                        "posting_date": entry.get("posting_date"),
                        "account": entry.get("account"),
                        "debit": entry.get("debit", 0),
                        "credit": entry.get("credit", 0),
                        "debit_in_account_currency": entry.get("debit_in_account_currency", 0),
                        "credit_in_account_currency": entry.get("credit_in_account_currency", 0),
                        "against": entry.get("against"),
                        "voucher_type": "POS Closing Shift",
                        "voucher_no": self.name,
                        "company": entry.get("company"),
                        "cost_center": entry.get("cost_center"),
                        "remarks": entry.get("remarks"),
                    })
                    gl_entry.insert(ignore_permissions=True)
                    
    def get_cash_account(self):
        # Get the default cash account from POS Profile or company settings
        return frappe.db.get_value("POS Profile", self.pos_profile, "write_off_account") or \
               frappe.db.get_value("Company", self.company, "default_cash_account")

    @frappe.whitelist()
    def get_payment_reconciliation_details(self):
        currency = frappe.get_cached_value("Company", self.company, "default_currency")
        return frappe.render_template(
            "posawesome/posawesome/doctype/pos_closing_shift/closing_shift_details.html",
            {"data": self, "currency": currency},
        )


@frappe.whitelist()
def get_cashiers(doctype, txt, searchfield, start, page_len, filters):
    cashiers_list = frappe.get_all("POS Profile User", filters=filters, fields=["user"])
    result = []
    for cashier in cashiers_list:
        user_email = frappe.get_value("User", cashier.user, "email")
        if user_email:
            result.append([cashier.user, f"{cashier.user} ({user_email})"])
    return result


@frappe.whitelist()
def get_pos_invoices(pos_opening_shift):
    submit_printed_invoices(pos_opening_shift)
    data = frappe.db.sql(
        """
        select
            name
        from
            `tabSales Invoice`
        where
            docstatus = 1 and posa_pos_opening_shift = %s
        """,
        (pos_opening_shift),
        as_dict=1,
    )

    data = [frappe.get_doc("Sales Invoice", d.name).as_dict() for d in data]
    return data


@frappe.whitelist()
def get_payments_entries(pos_opening_shift):
    return frappe.get_all(
        "Payment Entry",
        filters={
            "docstatus": 1,
            "reference_no": pos_opening_shift,
            "payment_type": "Receive",
        },
        fields=[
            "name",
            "mode_of_payment",
            "paid_amount",
            "reference_no",
            "posting_date",
            "party",
        ],
    )


@frappe.whitelist()
def make_closing_shift_from_opening(opening_shift, custom_cash_shortage=None, custom_cash_excess=None):
    opening_shift = json.loads(opening_shift)
    submit_printed_invoices(opening_shift.get("name"))
    closing_shift = frappe.new_doc("POS Closing Shift")
    closing_shift.pos_opening_shift = opening_shift.get("name")
    closing_shift.period_start_date = opening_shift.get("period_start_date")
    closing_shift.period_end_date = frappe.utils.get_datetime()
    closing_shift.pos_profile = opening_shift.get("pos_profile")
    closing_shift.user = opening_shift.get("user")
    closing_shift.company = opening_shift.get("company")
    closing_shift.grand_total = 0
    closing_shift.net_total = 0
    closing_shift.total_quantity = 0

    invoices = get_pos_invoices(opening_shift.get("name"))

    pos_transactions = []
    taxes = []
    payments = []
    pos_payments_table = []
    for detail in opening_shift.get("balance_details"):
        payments.append(
            frappe._dict(
                {
                    "mode_of_payment": detail.get("mode_of_payment"),
                    "opening_amount": detail.get("amount") or 0,
                    "expected_amount": detail.get("amount") or 0,
                }
            )
        )

    for d in invoices:
        pos_transactions.append(
            frappe._dict(
                {
                    "sales_invoice": d.name,
                    "posting_date": d.posting_date,
                    "grand_total": d.grand_total,
                    "customer": d.customer,
                }
            )
        )
        closing_shift.grand_total += flt(d.grand_total)
        closing_shift.net_total += flt(d.net_total)
        closing_shift.total_quantity += flt(d.total_qty)

        for t in d.taxes:
            existing_tax = [
                tx
                for tx in taxes
                if tx.account_head == t.account_head and tx.rate == t.rate
            ]
            if existing_tax:
                existing_tax[0].amount += flt(t.tax_amount)
            else:
                taxes.append(
                    frappe._dict(
                        {
                            "account_head": t.account_head,
                            "rate": t.rate,
                            "amount": t.tax_amount,
                        }
                    )
                )

        for p in d.payments:
            existing_pay = [
                pay for pay in payments if pay.mode_of_payment == p.mode_of_payment
            ]
            if existing_pay:
                cash_mode_of_payment = frappe.get_value(
                    "POS Profile",
                    opening_shift.get("pos_profile"),
                    "posa_cash_mode_of_payment",
                )
                if not cash_mode_of_payment:
                    cash_mode_of_payment = "Cash"
                if existing_pay[0].mode_of_payment == cash_mode_of_payment:
                    amount = p.amount - d.change_amount
                else:
                    amount = p.amount
                existing_pay[0].expected_amount += flt(amount)
            else:
                payments.append(
                    frappe._dict(
                        {
                            "mode_of_payment": p.mode_of_payment,
                            "opening_amount": 0,
                            "expected_amount": p.amount,
                        }
                    )
                )

    pos_payments = get_payments_entries(opening_shift.get("name"))

    for py in pos_payments:
        pos_payments_table.append(
            frappe._dict(
                {
                    "payment_entry": py.name,
                    "mode_of_payment": py.mode_of_payment,
                    "paid_amount": py.paid_amount,
                    "posting_date": py.posting_date,
                    "customer": py.party,
                }
            )
        )
        existing_pay = [
            pay for pay in payments if pay.mode_of_payment == py.mode_of_payment
        ]
        if existing_pay:
            existing_pay[0].expected_amount += flt(py.paid_amount)
        else:
            payments.append(
                frappe._dict(
                    {
                        "mode_of_payment": py.mode_of_payment,
                        "opening_amount": 0,
                        "expected_amount": py.paid_amount,
                    }
                )
            )

    closing_shift.set("pos_transactions", pos_transactions)
    closing_shift.set("payment_reconciliation", payments)
    closing_shift.set("taxes", taxes)
    closing_shift.set("pos_payments", pos_payments_table)

    return closing_shift


@frappe.whitelist()
def submit_closing_shift(closing_shift):
    closing_shift = json.loads(closing_shift)
    closing_shift_doc = frappe.get_doc(closing_shift)
    closing_shift_doc.flags.ignore_permissions = True
    closing_shift_doc.save()
    closing_shift_doc.submit()
    return closing_shift_doc.name


def submit_printed_invoices(pos_opening_shift):
    invoices_list = frappe.get_all(
        "Sales Invoice",
        filters={
            "posa_pos_opening_shift": pos_opening_shift,
            "docstatus": 0,
            "posa_is_printed": 1,
        },
    )
    for invoice in invoices_list:
        invoice_doc = frappe.get_doc("Sales Invoice", invoice.name)
        invoice_doc.submit()