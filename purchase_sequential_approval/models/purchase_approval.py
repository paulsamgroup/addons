from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection(
        selection_add=[
            ('submitted', 'Submitted for Approval'),
            ('ops_approved', 'Procurement Manager Approved'),
            ('finance_approved', 'Finance Manager Approved'),
        ],
        tracking=True
    )

    # Level 1 - Procurement Manager
    approved_ops_id = fields.Many2one('res.users', string="Procurement Manager Approved By", readonly=True)
    approval_date_ops = fields.Datetime(string="Procurement Manager Approval Date", readonly=True)

    # Level 2 - Finance Manager
    approved_finance_id = fields.Many2one('res.users', string="Finance Manager Approved By", readonly=True)
    approval_date_finance = fields.Datetime(string="Finance Manager Approval Date", readonly=True)

    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'approved_ops_id': False,
            'approval_date_ops': False,
            'approved_finance_id': False,
            'approval_date_finance': False,
        })
        return super(PurchaseOrder, self).copy(default)

    def action_submit_for_approval(self):
        for order in self:
            if order.state != 'draft':
                raise UserError(_("Only draft orders can be submitted for approval."))
            order.state = 'submitted'
            order.message_post(body=_("Purchase Order submitted for approval by %s") % self.env.user.name)

    def action_approve_ops(self):
        group_xmlid = 'purchase_sequential_approval.group_ops_manager'
        for order in self:
            if order.state != 'submitted':
                raise UserError(_('Order must be in Submitted state for Procurement Manager approval.'))
            if not self.env.user.has_group(group_xmlid):
                raise UserError(_('You are not authorized to approve as Procurement Manager.'))
            order.approved_ops_id = self.env.user
            order.approval_date_ops = fields.Datetime.now()
            order.state = 'ops_approved'
            order.message_post(body=_('Approved by Procurement Manager: %s') % self.env.user.name)

    def action_approve_finance(self):
        group_xmlid = 'purchase_sequential_approval.group_finance_manager'
        for order in self:
            if order.state != 'ops_approved':
                raise UserError(_('Order must be approved by Procurement Manager first.'))
            if not self.env.user.has_group(group_xmlid):
                raise UserError(_('You are not authorized to approve as Finance Manager.'))
            order.approved_finance_id = self.env.user
            order.approval_date_finance = fields.Datetime.now()
            order.state = 'finance_approved'
            order.message_post(body=_('Approved by Finance Manager: %s') % self.env.user.name)

    def action_reject(self, reason=None):
        allowed_groups = [
            'purchase_sequential_approval.group_ops_manager',
            'purchase_sequential_approval.group_finance_manager',
        ]
        for order in self:
            if not any(self.env.user.has_group(g) for g in allowed_groups):
                raise UserError(_('You are not authorized to reject this PO.'))
            order.state = 'draft'
            order.message_post(
                body=_('Purchase Order rejected by %s. %s') % (self.env.user.name, reason or '')
            )

    def button_confirm(self):
        for order in self:
            if order.state == 'finance_approved':
                order.state = 'draft'
                super(PurchaseOrder, order).button_confirm()
            elif order.state == 'draft':
                super(PurchaseOrder, order).button_confirm()
            else:
                raise UserError(_('Order must be Finance Approved to confirm.'))
        return True

    def button_reject(self):
        for order in self:
            order.action_reject()
        return True