# -*- coding: utf-8 -*-
"""
Migration 18.0.1.0.1 - Force recompute of payment status fields.

Needed because the @api.depends path changed from invoice_ids.payment_state
(which doesn't propagate through non-stored computed M2M fields) to the
correct stored path via order_line.invoice_lines.move_id.payment_state.
Stored values from the previous version must be refreshed.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    from odoo import api, SUPERUSER_ID

    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info(
        "abk_purchase_payment_status: recomputing payment status on all POs..."
    )
    orders = env['purchase.order'].search([])
    if orders:
        orders._compute_payment_status()
        orders._compute_abk_po_bill_status()
    _logger.info(
        "abk_purchase_payment_status: recompute done for %d POs.", len(orders)
    )
