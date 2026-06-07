from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sercop_auto_import = fields.Boolean(
        string='Importación Automática SERCOP',
        default=True,
        config_parameter='sercop.auto_import',
    )
    sercop_max_records = fields.Integer(
        string='Máximo de registros por importación',
        default=200,
        config_parameter='sercop.max_records',
    )
    sercop_create_leads = fields.Boolean(
        string='Crear oportunidades automáticamente',
        default=True,
        config_parameter='sercop.create_leads',
    )
