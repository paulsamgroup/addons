from odoo import models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class Picking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        StockQuant = self.env['stock.quant']

        for picking in self:

            # Only Delivery Orders
            if picking.picking_type_id.code != 'outgoing':
                continue

            no_stock_products = []

            for move in picking.move_ids_without_package:
                product = move.product_id
                rounding = product.uom_id.rounding

                # Check stock ONLY in the exact Source Location
                qty_available = sum(StockQuant.search([
                    ('product_id', '=', product.id),
                    ('location_id', '=', picking.location_id.id),
                ]).mapped('quantity'))

                if float_compare(qty_available, 0.0, precision_rounding=rounding) <= 0:
                    no_stock_products.append(product.display_name)

            if no_stock_products:
                raise UserError(_(
                    "The following products have no available stock in the selected Source Location:\n\n%s"
                ) % ("\n".join(no_stock_products)))

        return super().button_validate()