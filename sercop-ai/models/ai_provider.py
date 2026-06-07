from odoo import models, fields, api, _


class SercopAiProvider(models.Model):
    _name = 'sercop.ai.provider'
    _description = 'Proveedor de IA para SERCOP'
    _rec_name = 'name'
    _order = 'is_default desc, name asc'

    name = fields.Char(string='Nombre', required=True)
    provider_type = fields.Selection([
        ('ollama', 'Ollama (Local - Gratuito)'),
        ('openai', 'OpenAI'),
    ], string='Proveedor', required=True, default='ollama')
    endpoint_url = fields.Char(
        string='URL Endpoint',
        default='http://localhost:11434',
        help='Ollama: http://localhost:11434\nOpenAI: https://api.openai.com/v1',
    )
    api_key = fields.Char(
        string='API Key',
        help='Solo necesario para OpenAI',
    )
    model_name = fields.Char(
        string='Modelo',
        required=True,
        default='deepseek-r1:7b',
        help='Ollama: deepseek-r1:7b, llama3:8b, mistral:7b\nOpenAI: gpt-4, gpt-3.5-turbo',
    )
    temperature = fields.Float(string='Temperatura', default=0.3)
    max_tokens = fields.Integer(string='Máx tokens salida', default=4096)
    is_default = fields.Boolean(string='Proveedor por defecto')
    active = fields.Boolean(string='Activo', default=True)

    @api.constrains('is_default')
    def _check_default(self):
        for record in self:
            if record.is_default:
                others = self.search([('is_default', '=', True), ('id', '!=', record.id)])
                if others:
                    others.write({'is_default': False})
