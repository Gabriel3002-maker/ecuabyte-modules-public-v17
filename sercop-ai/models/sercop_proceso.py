import json
import base64
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import fitz
except ImportError:
    fitz = None


class SercopProceso(models.Model):
    _inherit = 'sercop.proceso'

    state = fields.Selection([
        ('imported', 'Importado'),
        ('reviewed', 'Revisado'),
        ('sent_to_crm', 'Enviado a CRM'),
    ], string='Estado de Revisión', default='imported', tracking=True)
    document_ids = fields.One2many('sercop.document', 'proceso_id', string='Documentos')
    proforma_ids = fields.One2many('sale.order', 'sercop_proceso_id', string='Cotizaciones')

    def _create_lead_from_proceso(self):
        lead = super()._create_lead_from_proceso()
        if lead:
            self.write({'state': 'sent_to_crm'})
        return lead

    def action_review(self):
        self.ensure_one()
        if self.state != 'imported':
            raise UserError(_('Solo los procesos en estado "Importado" pueden marcarse como revisados.'))
        self.write({'state': 'reviewed'})
        return True

    def action_send_to_crm(self):
        self.ensure_one()
        if self.state == 'sent_to_crm' and self.lead_id:
            return self.action_open_lead()
        if self.state != 'reviewed':
            raise UserError(_('El proceso debe estar en estado "Revisado" para enviar a CRM.'))
        lead = self._create_lead_from_proceso()
        if lead:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'crm.lead',
                'res_id': lead.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return True

    @api.model
    def cron_importar_procesos(self):
        _logger.info('Inicio de importación SERCOP automática (sercop-ai)')
        imported = self.fetch_sercop_data()
        pendientes = self.search([('state', '=', 'reviewed'), ('es_tecnologia', '=', True)])
        lead_count = 0
        for proceso in pendientes:
            try:
                proceso._create_lead_from_proceso()
                lead_count += 1
            except Exception as e:
                _logger.error('Error creando lead para %s: %s', proceso.codigo_contratacion, str(e))
        _logger.info('Importación SERCOP completada: %d procesos, %d leads', imported, lead_count)
        return True

    def action_reset_leads(self):
        procesos = self.search([('lead_id', '!=', False)])
        leads_to_delete = procesos.mapped('lead_id')
        if leads_to_delete:
            leads_to_delete.unlink()
        procesos.write({
            'lead_id': False,
            'state': 'imported',
        })
        return True

    def action_generate_quotation_ai(self):
        self.ensure_one()
        if not self.document_ids:
            raise UserError(_('Debe subir al menos un documento (Informe de Necesidad o Términos de Referencia) antes de generar la cotización.'))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ai.quotation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_proceso_id': self.id,
                'default_ai_provider_id': self._get_default_provider().id,
            },
        }

    def _get_default_provider(self):
        provider = self.env['sercop.ai.provider'].search([('is_default', '=', True)], limit=1)
        if not provider:
            provider = self.env['sercop.ai.provider'].search([], limit=1)
        if not provider:
            raise UserError(_('No hay proveedores de IA configurados. Vaya a Ajustes > SERCOP IA y configure uno.'))
        return provider

    def _extract_pdf_text(self, document):
        if fitz is None:
            raise UserError(_('PyMuPDF no está instalado. Ejecute: pip install PyMuPDF'))
        file_data = base64.b64decode(document.file)
        doc = fitz.open(stream=file_data, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text[:1500]

    def _build_ai_prompt(self, provider):
        textos = []
        for doc in self.document_ids:
            try:
                texto = self._extract_pdf_text(doc)
                textos.append(f"=== {doc.name} ({dict(doc._fields['document_type'].selection).get(doc.document_type, 'Documento')}) ===\n{texto}")
            except Exception as e:
                textos.append(f"=== {doc.name} ===\n[Error al leer PDF: {str(e)}]")

        prompt = f"""Eres un experto en contratación pública ecuatoriana (SERCOP) y generación de proformas comerciales.

DATOS DEL PROCESO:
- Entidad: {self.entidad_contratante or 'N/A'}
- Objeto de contratación: {self.objeto_contratacion or 'N/A'}
- Tipo de necesidad: {self.tipo_necesidad or 'N/A'}
- Cantidad: {self.cantidad or 'N/A'}
- Provincia: {self.provincia or 'N/A'}
- Código NIC: {self.codigo_contratacion or 'N/A'}

DOCUMENTOS ADJUNTOS:
{' '.join(textos)}

INSTRUCCIONES:
1. Analiza el objeto de contratación y todos los documentos adjuntos en detalle.
2. Identifica los productos y servicios específicos que se requieren para esta contratación.
3. Genera una cotización profesional para presentar a la entidad contratante.
4. IMPORTANTE: Incluye notas sobre requisitos legales y técnicos clave para evitar incumplimientos y multas según la normativa SERCOP.
5. Sugiere condiciones de pago, plazos de entrega y validez de oferta realistas.

Responde SOLO con JSON válido (sin markdown, sin explicaciones adicionales):
{{
  "lineas": [
    {{"descripcion": "string con descripción detallada del producto/servicio", "cantidad": 1, "unidad": "string (ej: Global, Unidad, Mes)", "precio_unitario": 0.00}}
  ],
  "condiciones_pago": "string",
  "validez_oferta": "string (ej: 30 días calendario)",
  "tiempo_entrega": "string",
  "notas_legales": ["string con requisito legal importante", "otra nota legal"],
  "consideraciones_tecnicas": ["string con especificación técnica", "otra consideración"],
  "observaciones": "string con información adicional relevante"
}}"""
        return prompt

    def _call_ai(self, prompt, provider=None):
        if not provider:
            provider = self._get_default_provider()
        headers = {'Content-Type': 'application/json'}
        payload = {}
        system_msg = 'Eres un experto en contratación pública ecuatoriana y generación de proformas. Responde SOLO con JSON válido, sin explicaciones, sin markdown.'
        if provider.provider_type == 'ollama':
            url = provider.endpoint_url.rstrip('/') + '/api/chat'
            payload = {
                'model': provider.model_name,
                'messages': [
                    {'role': 'system', 'content': system_msg},
                    {'role': 'user', 'content': prompt},
                ],
                'stream': False,
                'format': 'json',
                'options': {
                    'temperature': provider.temperature,
                    'num_predict': provider.max_tokens,
                },
            }
        elif provider.provider_type == 'openai':
            url = provider.endpoint_url.rstrip('/') + '/chat/completions'
            headers['Authorization'] = f'Bearer {provider.api_key}'
            payload = {
                'model': provider.model_name,
                'messages': [
                    {'role': 'system', 'content': system_msg},
                    {'role': 'user', 'content': prompt},
                ],
                'temperature': provider.temperature,
                'max_tokens': provider.max_tokens,
            }
        else:
            raise UserError(_('Tipo de proveedor IA no soportado: %s') % provider.provider_type)
        try:
            import requests
            response = requests.post(url, json=payload, headers=headers, timeout=300)
            response.raise_for_status()
            data = response.json()
            if provider.provider_type == 'ollama':
                content = data.get('message', {}).get('content', '')
            else:
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            content = content.strip()
            for prefix in ['```json', '```']:
                if content.startswith(prefix):
                    content = content[len(prefix):]
            for suffix in ['```']:
                if content.endswith(suffix):
                    content = content[:-len(suffix)]
            content = content.strip()
            if content.startswith('{') or content.startswith('['):
                return json.loads(content)
            import re
            json_match = re.search(r'(\{.*\}|\[.*\])', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            raise UserError(_('No se encontró JSON válido en la respuesta:\n%s') % content[:500])
        except json.JSONDecodeError as e:
            raise UserError(_('Error al interpretar la respuesta de la IA. Respuesta recibida:\n%s\n\nError: %s') % (content[:500], str(e)))
        except requests.exceptions.ConnectionError:
            raise UserError(_('No se pudo conectar con %s en %s. Verifique que el servicio esté corriendo.') % (provider.name, provider.endpoint_url))
        except requests.exceptions.Timeout:
            raise UserError(_('La IA tardó demasiado en responder. Intente con un modelo más rápido o reduzca el tamaño de los documentos.'))
        except Exception as e:
            raise UserError(_('Error al llamar a la IA: %s') % str(e))

    def _buscar_o_crear_producto(self, descripcion, precio_unitario):
        Product = self.env['product.product']
        product = Product.search([
            ('name', 'ilike', descripcion.strip()),
            ('type', '=', 'service'),
        ], limit=1)
        if not product:
            product = Product.search([
                ('name', 'ilike', descripcion.strip()[:50]),
            ], limit=1)
        if not product:
            product = Product.create({
                'name': descripcion.strip()[:200],
                'type': 'service',
                'list_price': precio_unitario,
                'sale_ok': True,
                'purchase_ok': False,
            })
        return product

    def _create_quotation_from_ai(self, ai_response):
        self.ensure_one()
        partner = self.env['res.partner'].search([('name', '=', self.entidad_contratante)], limit=1)
        if not partner and self.entidad_contratante:
            partner = self.env['res.partner'].create({
                'name': self.entidad_contratante,
                'email': self.email_contacto,
                'phone': self.telefono_contacto,
            })

        notas = ''
        if ai_response.get('notas_legales'):
            notas += 'NOTAS LEGALES:\n' + '\n'.join('- ' + n for n in ai_response['notas_legales']) + '\n\n'
        if ai_response.get('consideraciones_tecnicas'):
            notas += 'CONSIDERACIONES TÉCNICAS:\n' + '\n'.join('- ' + n for n in ai_response['consideraciones_tecnicas']) + '\n\n'
        if ai_response.get('observaciones'):
            notas += 'OBSERVACIONES:\n' + ai_response['observaciones'] + '\n\n'
        if ai_response.get('condiciones_pago'):
            notas += 'CONDICIONES DE PAGO:\n' + ai_response['condiciones_pago'] + '\n'
        if ai_response.get('validez_oferta'):
            notas += 'VALIDEZ DE OFERTA: ' + ai_response['validez_oferta'] + '\n'
        if ai_response.get('tiempo_entrega'):
            notas += 'TIEMPO DE ENTREGA: ' + ai_response['tiempo_entrega'] + '\n'

        order_lines = []
        for linea in ai_response.get('lineas', []):
            product = self._buscar_o_crear_producto(linea.get('descripcion', ''), linea.get('precio_unitario', 0))
            order_lines.append((0, 0, {
                'product_id': product.id,
                'name': linea.get('descripcion', product.name),
                'product_uom_qty': linea.get('cantidad', 1),
                'price_unit': linea.get('precio_unitario', 0),
            }))

        quotation = self.env['sale.order'].create({
            'partner_id': partner.id if partner else False,
            'origin': f'SERCOP: {self.codigo_contratacion}',
            'sercop_proceso_id': self.id,
            'order_line': order_lines,
            'note': notas.strip(),
            'state': 'draft',
        })
        return quotation
