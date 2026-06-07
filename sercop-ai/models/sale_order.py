from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sercop_proceso_id = fields.Many2one('sercop.proceso', string='Proceso SERCOP', readonly=True)
