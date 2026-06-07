from odoo import models, fields, api


class SercopDocument(models.Model):
    _name = 'sercop.document'
    _description = 'Documento SERCOP'
    _rec_name = 'name'
    _order = 'create_date desc'

    name = fields.Char(string='Nombre', required=True)
    proceso_id = fields.Many2one('sercop.proceso', string='Proceso SERCOP', ondelete='cascade')
    lead_id = fields.Many2one('crm.lead', string='Oportunidad CRM', ondelete='set null')
    file = fields.Binary(string='Archivo', attachment=True, required=True)
    filename = fields.Char(string='Nombre del Archivo')
    document_type = fields.Selection([
        ('informe', 'Informe de Necesidad'),
        ('terminos', 'Términos de Referencia'),
        ('autorizacion', 'Autorización'),
        ('otros', 'Otros'),
    ], string='Tipo de Documento', default='otros')
    active = fields.Boolean(string='Activo', default=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') and vals.get('filename'):
                vals['name'] = vals['filename']
            if vals.get('proceso_id') and not vals.get('lead_id'):
                proceso = self.env['sercop.proceso'].browse(vals['proceso_id'])
                if proceso.lead_id:
                    vals['lead_id'] = proceso.lead_id.id
        return super().create(vals_list)

    def action_download(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self.id}?model=sercop.document&field=file&filename_field=filename',
            'target': 'new',
        }
