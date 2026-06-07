from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SercopImportWizard(models.TransientModel):
    _name = 'sercop.import.wizard'
    _description = 'Asistente de Importación SERCOP'

    search_term = fields.Char(
        string='Término de búsqueda',
        help='Dejar vacío para buscar todas las palabras clave configuradas',
    )
    create_leads = fields.Boolean(string='Crear oportunidades', default=True)
    max_records = fields.Integer(string='Máximo de registros', default=100)
    import_count = fields.Integer(string='Importados', default=0, readonly=True)
    lead_count = fields.Integer(string='Oportunidades creadas', default=0, readonly=True)
    state = fields.Selection([
        ('choose', 'Configurar'),
        ('result', 'Resultado'),
    ], default='choose')

    def action_import(self):
        self.ensure_one()
        Proceso = self.env['sercop.proceso']
        if self.search_term:
            imported = Proceso.fetch_sercop_data(
                search_term=self.search_term,
                max_records=self.max_records,
            )
        else:
            imported = Proceso.fetch_sercop_data(
                max_records=self.max_records,
            )
        self.import_count = imported
        if self.create_leads:
            nuevos = Proceso.search([
                ('lead_creado', '=', False),
                ('es_tecnologia', '=', True),
            ], limit=self.max_records)
            count = 0
            for p in nuevos:
                try:
                    p._create_lead_from_proceso()
                    count += 1
                except Exception:
                    pass
            self.lead_count = count
        self.state = 'result'
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sercop.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
