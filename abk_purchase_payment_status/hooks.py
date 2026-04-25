# -*- coding: utf-8 -*-

import logging

_logger = logging.getLogger(__name__)


def post_migrate(env):
    """Force recompute of payment status fields on all purchase orders.

    This is needed when upgrading from a version where the stored computed
    fields may hold stale values due to the dependency path change.
    """
    _logger.info("abk_purchase_payment_status: recomputing payment status on all POs...")
    orders = env['purchase.order'].search([])
    if orders:
        orders._compute_payment_status()
        orders._compute_abk_po_bill_status()
    _logger.info("abk_purchase_payment_status: recompute done for %d POs.", len(orders))
