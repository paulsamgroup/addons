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
                line_names = ', '.join(
                    missing_lines.mapped(lambda line: line.product_id.display_name or line.name or str(line.sequence))
                )
                raise ValidationError(_(
                    'Please fill Analytic Distribution on all purchase order lines before continuing. Missing lines: %s',
                    line_names,
                ))

    def button_confirm(self):
        self._check_required_analytic_distribution()
        return super().button_confirm()