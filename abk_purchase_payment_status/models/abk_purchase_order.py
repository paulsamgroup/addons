"""
Module to extend purchase order functionality with payment status tracking.
"""

from odoo import models, fields, api


class PurchaseOrder(models.Model):
    """
    Extends the purchase.order model to include payment status and amount paid tracking.
    """
    _inherit = 'purchase.order'

    abk_payment_status = fields.Selection(
        [
            ('not_paid', 'Not Paid'),
            ('in_payment', 'In Payment'),
            ('partial', 'Partially Paid'),
            ('paid', 'Paid'),
            ('reversed', 'Reversed'),
            ('nothing', 'Bill Not Created')
        ],
        string="Payment Status",
        compute="_compute_payment_status",
        copy=False,
        store=True,
        readonly=True,
        default="nothing"
    )

    @api.depends('invoice_ids', 'invoice_ids.state', 'invoice_ids.move_type', 'invoice_ids.payment_state')
    def _compute_payment_status(self):
        """
        Mirror the vendor bill payment_state on the PO. If no bill exists,
        show Bill Not Created.
        """
        for rec in self:
            bills = rec.invoice_ids.filtered(
                lambda inv: inv.move_type == 'in_invoice' and inv.state != 'cancel'
            )
            if bills:
                payment_states = bills.mapped('payment_state')
                if 'in_payment' in payment_states:
                    rec.abk_payment_status = 'in_payment'
                elif 'partial' in payment_states:
                    rec.abk_payment_status = 'partial'
                elif all(state == 'paid' for state in payment_states):
                    rec.abk_payment_status = 'paid'
                elif all(state == 'reversed' for state in payment_states):
                    rec.abk_payment_status = 'reversed'
                elif 'not_paid' in payment_states and any(
                    state in ('paid', 'in_payment', 'partial', 'reversed')
                    for state in payment_states
                ):
                    rec.abk_payment_status = 'partial'
                else:
                    rec.abk_payment_status = 'not_paid'
            else:
                rec.abk_payment_status = 'nothing'

    abk_po_bill_status = fields.Char(
        string="Status",
        compute="_compute_abk_po_bill_status",
        store=True,
        readonly=True,
    )

    @api.depends('state', 'invoice_ids', 'invoice_ids.state', 'invoice_ids.payment_state', 'invoice_ids.move_type')
    def _compute_abk_po_bill_status(self):
        """
        Show the bill's payment_state when posted vendor bills exist,
        otherwise fall back to the PO's own state.
        """
        for rec in self:
            posted_bills = rec.invoice_ids.filtered(
                lambda inv: inv.state == 'posted' and inv.move_type == 'in_invoice'
            )
            if posted_bills:
                payment_states = posted_bills.mapped('payment_state')
                if 'in_payment' in payment_states:
                    rec.abk_po_bill_status = 'in_payment'
                elif all(s in ('paid', 'reversed') for s in payment_states):
                    rec.abk_po_bill_status = 'paid'
                elif 'partial' in payment_states:
                    rec.abk_po_bill_status = 'partial'
                else:
                    rec.abk_po_bill_status = 'not_paid'
            else:
                rec.abk_po_bill_status = rec.state

    abk_amount_paid = fields.Float(
        compute='_compute_abk_amount_paid',
        string="Amount Paid",
        copy=False
    )

    @api.depends('invoice_ids', 'abk_payment_status', 'invoice_status')
    def _compute_abk_amount_paid(self):
        """
        Compute the total amount paid based on posted invoices and their payment states.
        """
        for order in self:
            order.abk_amount_paid = 0.0
            for invoice in order.invoice_ids:
                if (invoice.state == 'posted' and
                    invoice.move_type == 'in_invoice' and
                    invoice.payment_state in ('in_payment', 'paid', 'partial', 'reversed')):
                    order.abk_amount_paid += invoice.amount_total - invoice.amount_residual
                if (invoice.state == 'posted' and
                    invoice.move_type == 'in_refund' and
                    invoice.payment_state in ('in_payment', 'paid', 'partial', 'reversed')):
                    order.abk_amount_paid -= invoice.amount_total - invoice.amount_residual