import json
import logging
import threading

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AiQuotationWizard(models.TransientModel):
    _name = 'ai.quotation.wizard'
    _description = 'Generar Cotización con IA'

    proceso_id = fields.Many2one('sercop.proceso', string='Proceso', required=True, readonly=True)
    ai_provider_id = fields.Many2one('sercop.ai.provider', string='Proveedor IA', required=True)
    ai_response_json = fields.Text(string='Respuesta de la IA (JSON)')
    quotation_id = fields.Many2one('sale.order', string='Cotización generada', readonly=True)
    state = fields.Selection([
        ('config', 'Configurar'),
        ('processing', 'Procesando...'),
        ('preview', 'Previsualizar'),
        ('done', 'Completado'),
        ('error', 'Error'),
    ], string='Estado', default='config', required=True)
    error_message = fields.Text(string='Error', readonly=True)
    lineas_json = fields.Text(string='Líneas de cotización (JSON)')
    proceso_id_has_docs = fields.Char(string='Documentos', compute='_compute_proceso_docs')

    @api.depends('proceso_id')
    def _compute_proceso_docs(self):
        for rec in self:
            if rec.proceso_id and rec.proceso_id.document_ids:
                names = [d.name for d in rec.proceso_id.document_ids]
                rec.proceso_id_has_docs = ', '.join(names)
            else:
                rec.proceso_id_has_docs = 'Sin documentos adjuntos'

    @api.onchange('proceso_id')
    def _onchange_proceso_id(self):
        if self.proceso_id:
            provider = self.proceso_id._get_default_provider()
            self.ai_provider_id = provider

    def action_analyze(self):
        self.ensure_one()
        if not self.proceso_id.document_ids:
            raise UserError(_('Debe subir al menos un documento al proceso antes de analizar.'))
        self.write({'state': 'processing', 'error_message': False})
        self.env.cr.commit()
        _logger.info('Iniciando análisis IA en segundo plano para wizard %s', self.id)
        thread = threading.Thread(
            target=self._run_ai_analysis_thread,
            args=(self.pool, self._uid, dict(self._context), self.id),
            daemon=True,
        )
        thread.start()
        return self._reload_wizard()

    @classmethod
    def _run_ai_analysis_thread(cls, pool, uid, context, wizard_id):
        try:
            with pool.cursor() as cr:
                env = api.Environment(cr, uid, context)
                wizard = env['ai.quotation.wizard'].browse(wizard_id)
                if not wizard.exists():
                    _logger.warning('Wizard %s no existe', wizard_id)
                    return
                proceso = wizard.proceso_id
                prompt = proceso._build_ai_prompt(wizard.ai_provider_id)
                _logger.info('Prompt length: %d chars', len(prompt))
                result = proceso._call_ai(prompt, wizard.ai_provider_id)
                _logger.info('AI result keys: %s', list(result.keys()) if isinstance(result, dict) else type(result))
                _logger.info('AI result (truncated): %s', json.dumps(result, ensure_ascii=False)[:2000])
                lineas = []
                if isinstance(result, list):
                    lineas = result
                elif isinstance(result, dict):
                    if 'lineas' in result and isinstance(result['lineas'], list):
                        lineas = result['lineas']
                    else:
                        for key in ['productos', 'items', 'servicios', 'articulos', 'productos_servicios']:
                            if result.get(key, []) and isinstance(result[key], list):
                                lineas = result[key]
                                break
                        if not lineas and 'descripcion' in result:
                            lineas = [result]
                wizard.write({
                    'ai_response_json': json.dumps(result, indent=2, ensure_ascii=False),
                    'lineas_json': json.dumps(lineas, indent=2, ensure_ascii=False),
                    'state': 'preview',
                })
                cr.commit()
                _logger.info('Análisis IA completado para wizard %s', wizard_id)
        except Exception as e:
            _logger.error('Error en análisis IA en thread: %s', str(e), exc_info=True)
            try:
                with pool.cursor() as cr:
                    env = api.Environment(cr, uid, context)
                    wizard = env['ai.quotation.wizard'].browse(wizard_id)
                    if wizard.exists():
                        wizard.write({
                            'state': 'error',
                            'error_message': f'{type(e).__name__}: {str(e)}',
                        })
                        cr.commit()
            except Exception as db_err:
                _logger.error('Error al guardar estado de error: %s', db_err)

    def action_check_result(self):
        self.ensure_one()
        return self._reload_wizard()

    def action_retry(self):
        self.ensure_one()
        self.write({'state': 'config', 'error_message': False})
        return self._reload_wizard()

    def _reload_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ai.quotation.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_create_quotation(self):
        self.ensure_one()
        ai_response = json.loads(self.ai_response_json)
        try:
            lineas = json.loads(self.lineas_json)
        except json.JSONDecodeError:
            lineas = ai_response.get('lineas', [])
        ai_response['lineas'] = lineas
        quotation = self.proceso_id._create_quotation_from_ai(ai_response)
        self.write({'quotation_id': quotation.id, 'state': 'done'})
        return self._reload_wizard()

    def action_open_quotation(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': self.quotation_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
