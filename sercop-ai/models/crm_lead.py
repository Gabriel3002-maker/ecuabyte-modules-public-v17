from odoo import models, fields


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    sercop_document_ids = fields.One2many('sercop.document', 'lead_id', string='Documentos SERCOP')
    sercop_proceso_id = fields.Many2one('sercop.proceso', string='Proceso SERCOP', related='sercop_document_ids.proceso_id', readonly=True)
