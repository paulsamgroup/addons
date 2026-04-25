from odoo import _, models
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _check_required_analytic_distribution(self):
        for order in self:
            missing_lines = order.order_line.filtered(
                lambda line: not line.display_type and not line.is_downpayment and not line.analytic_distribution
            )
            if missing_lines:
                raise ValidationError(_(
                    'Please fill in the Analytic Distribution for all order lines before confirming.'
                ))

    def button_confirm(self):
        self._check_required_analytic_distribution()
        return super().button_confirm()