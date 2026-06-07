from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sercop_ai_provider_id = fields.Many2one(
        'sercop.ai.provider',
        string='Proveedor IA por defecto',
        config_parameter='sercop_ai.provider_id',
    )
    sercop_auto_quotation = fields.Boolean(
        string='Generar cotización automática',
        help='Generar automáticamente una cotización borrador cuando se envía un proceso a CRM',
        config_parameter='sercop_ai.auto_quotation',
        default=False,
    )
