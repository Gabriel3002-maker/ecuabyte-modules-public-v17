import requests
import logging
import json
import re
from datetime import datetime, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

SERCOP_API_URL = "https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/NCO/NCORetornaRegistros.cpe"
SERCOP_DETALLE_URL = "https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/NCO/NCORegistroDetalle.cpe"

KEYWORDS_TECNOLOGIA = [
    'software', 'hosting', 'servidor', 'servidores', 'aplicacion', 'aplicaciones',
    'sistema', 'sistemas', 'informatico', 'informatica', 'tecnologia', 'tecnológico',
    'plataforma', 'licencia', 'licencias', 'dominio', 'dominios', 'certificado ssl',
    'pagina web', 'pagina web', 'desarrollo', 'programacion', 'base de datos',
    'mantenimiento de software', 'soporte tecnico', 'soporte técnico',
    'red', 'redes', 'conectividad', 'firewall', 'antivirus', 'ciberseguridad',
    'computador', 'computador', 'laptop', 'pc', 'equipo informatico',
    'aplicativo', 'aplicativos', 'api', 'interfaz', 'migracion', 'migración',
    'data center', 'cloud', 'nube', 'correo', 'email', 'outlook',
    'impresora', 'impresoras', 'toner', 'cartucho', 'suministro informatico',
    'ups', 'estabilizador', 'switch', 'router', 'acceso point',
    'sistema operativo', 'windows', 'linux',
    'cctv', 'camara', 'camaras', 'videovigilancia',
    'consulta', 'consultoria informatica', 'consultoría',
    'actualizacion', 'actualización', 'implementacion', 'implementación',
    'automatizacion', 'automatización',
    'erp', 'crm', 'contable', 'facturacion', 'facturación',
    'hardware', 'disco duro', 'ssd', 'memoria ram', 'servicio tecnico',
    'instalacion', 'instalación', 'configuracion', 'configuración',
    'suscripcion', 'suscripción', 'arriendo de software',
    'telecomunicaciones', 'fibra optica', 'internet', 'wifi',
    'siem', 'seguridad informatica', 'seguridad de la informacion',
]


class SercopProceso(models.Model):
    _name = 'sercop.proceso'
    _description = 'Proceso de Contratación SERCOP'
    _rec_name = 'codigo_contratacion'
    _order = 'fecha_publicacion desc'

    codigo_contratacion = fields.Char(string='Código NIC', required=True, index=True)
    tipo_necesidad = fields.Char(string='Tipo de Necesidad')
    fecha_publicacion = fields.Datetime(string='Fecha de Publicación')
    fecha_limite_propuesta = fields.Datetime(string='Fecha Límite')
    provincia = fields.Char(string='Provincia - Cantón')
    canton = fields.Char(string='Cantón')
    objeto_contratacion = fields.Text(string='Objeto de Contratación')
    estado = fields.Char(string='Estado')
    entidad_contratante = fields.Char(string='Entidad Contratante')
    direccion_entrega = fields.Text(string='Dirección de Entrega')
    contacto = fields.Text(string='Contacto')
    funcionario = fields.Char(string='Funcionario Encargado')
    email_contacto = fields.Char(string='Email Contacto')
    telefono_contacto = fields.Char(string='Teléfono Contacto')
    url_detalle = fields.Char(string='URL Detalle')
    url_entidad = fields.Char(string='URL Entidad')
    valor_unitario = fields.Float(string='Valor Unitario', digits=(12, 5))
    cantidad = fields.Float(string='Cantidad', digits=(12, 2))
    seq_tipo_necesidad = fields.Char(string='Seq Tipo Necesidad')
    seq_estado = fields.Char(string='Seq Estado')
    tcom_necesidad_contratacion_id = fields.Char(string='ID Necesidad')
    es_tecnologia = fields.Boolean(string='Relacionado a Tecnología', default=False)
    lead_id = fields.Many2one('crm.lead', string='Oportunidad CRM', readonly=True)
    lead_creado = fields.Boolean(string='Oportunidad Creada', default=False, readonly=True)
    active = fields.Boolean(string='Activo', default=True)

    @api.model
    def _get_api_params(self, start=0, length=100, search_value=''):
        params = {
            'sEcho': '1',
            'iColumns': '10',
            'sColumns': '',
            'iDisplayStart': str(start),
            'iDisplayLength': str(length),
            'sSearch': '',
            'bRegex': 'false',
            'iSortCol_0': '1',
            'sSortDir_0': 'desc',
            'mDataProp_0': 'tipo_necesidad',
            'mDataProp_1': 'codigo_contratacion',
            'mDataProp_2': 'fecha_publicacion',
            'mDataProp_3': 'provincia',
            'mDataProp_4': 'objeto_contratacion',
            'mDataProp_5': 'estado',
            'mDataProp_6': 'fecha_limite_propuesta',
            'mDataProp_7': 'url',
            'mDataProp_8': 'direccion_entrega',
            'mDataProp_9': 'contacto',
            'sSearch_4': search_value,
            'bRegex_4': 'false',
            'bSearchable_4': 'true',
            'bSortable_4': 'false',
        }
        return params

    def _parse_registro(self, registro):
        url_entidad = ''
        url_detalle = ''
        if registro.get('url'):
            m = re.search(r'href=([^\s>]+)', registro['url'])
            if m:
                url_entidad = 'https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/' + m.group(1)

        vals = {
            'codigo_contratacion': registro.get('codigo_contratacion', '').strip(),
            'tipo_necesidad': registro.get('tipo_necesidad', ''),
            'fecha_publicacion': self._parse_fecha(registro.get('fecha_publicacion')),
            'fecha_limite_propuesta': self._parse_fecha(registro.get('fecha_limite_propuesta')),
            'provincia': registro.get('provincia', ''),
            'canton': registro.get('canton', ''),
            'objeto_contratacion': registro.get('objeto_contratacion', ''),
            'estado': registro.get('estado', ''),
            'entidad_contratante': registro.get('razon_social', ''),
            'direccion_entrega': registro.get('direccion_entrega', ''),
            'funcionario': registro.get('funcionario_encargado', ''),
            'email_contacto': registro.get('email_encargado', ''),
            'telefono_contacto': registro.get('telefono_encargado', ''),
            'contacto': registro.get('contacto', ''),
            'url_detalle': url_detalle,
            'url_entidad': url_entidad,
            'valor_unitario': float(registro.get('valor_unitario', 0) or 0),
            'cantidad': float(registro.get('cantidad', 0) or 0),
            'seq_tipo_necesidad': registro.get('seq_tipo_necesidad', ''),
            'seq_estado': registro.get('seq_estado', ''),
            'tcom_necesidad_contratacion_id': registro.get('tcom_necesidad_contratacion_id', ''),
        }
        return vals

    def _parse_fecha(self, fecha_str):
        if not fecha_str:
            return False
        try:
            return datetime.strptime(fecha_str.strip(), '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            return False

    def _es_tecnologia(self, texto):
        if not texto:
            return False
        texto_upper = texto.upper()
        keyword_obj = self.env['sercop.keyword'].search([])
        if keyword_obj:
            for kw in keyword_obj:
                if kw.name.upper() in texto_upper:
                    return True
            return False
        for kw in KEYWORDS_TECNOLOGIA:
            if kw.upper() in texto_upper:
                return True
        return False

    @api.model
    def fetch_sercop_data(self, search_term='', max_records=200):
        imported = 0
        start = 0
        page_size = 100
        if not search_term:
            keywords = self.env['sercop.keyword'].search([])
            if keywords:
                for keyword in keywords:
                    imported += self._fetch_by_keyword(keyword.name, max_records)
            else:
                for kw in KEYWORDS_TECNOLOGIA:
                    imported += self._fetch_by_keyword(kw, max_records)
        else:
            imported = self._fetch_by_keyword(search_term, max_records)
        return imported

    def _fetch_by_keyword(self, keyword, max_records=200):
        imported = 0
        start = 0
        page_size = 100
        seen = set()

        while start < max_records:
            try:
                params = self._get_api_params(start=start, length=page_size, search_value=keyword)
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'Accept': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (compatible; Odoo/17.0)',
                }
                _logger.info('Fetching SERCOP data: keyword=%s, start=%d, length=%d', keyword, start, page_size)
                res = requests.post(
                    SERCOP_API_URL,
                    params={'lot': '1'},
                    data=params,
                    headers=headers,
                    timeout=30,
                )
                res.raise_for_status()
                data = res.json()
                registros = data.get('data', [])
                if not registros:
                    break
                for reg in registros:
                    codigo = reg.get('codigo_contratacion', '').strip()
                    if not codigo or codigo in seen:
                        continue
                    seen.add(codigo)
                    vals = self._parse_registro(reg)
                    vals['es_tecnologia'] = self._es_tecnologia(
                        vals.get('objeto_contratacion', '') + ' ' + vals.get('entidad_contratante', '')
                    )
                    existing = self.search([('codigo_contratacion', '=', codigo)], limit=1)
                    if existing:
                        if existing.estado != vals.get('estado'):
                            existing.write(vals)
                            imported += 1
                    else:
                        self.create(vals)
                        imported += 1
                if len(registros) < page_size:
                    break
                start += page_size
            except requests.exceptions.RequestException as e:
                _logger.error('Error fetching SERCOP data: %s', str(e))
                break
            except Exception as e:
                _logger.error('Error processing SERCOP data: %s', str(e))
                break
        return imported

    def action_create_lead(self):
        self.ensure_one()
        if self.lead_creado and self.lead_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'crm.lead',
                'res_id': self.lead_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
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

    def _create_lead_from_proceso(self):
        self.ensure_one()
        if self.lead_creado:
            return self.lead_id
        team = self.env['crm.team'].search([('name', 'ilike', 'Tecnolog')], limit=1)
        partner = self.env['res.partner'].search([('name', '=', self.entidad_contratante)], limit=1)
        if not partner and self.entidad_contratante:
            partner = self.env['res.partner'].create({
                'name': self.entidad_contratante,
                'email': self.email_contacto,
                'phone': self.telefono_contacto,
                'comment': self.direccion_entrega,
            })
        description = (
            f"Objeto de Contratación: {self.objeto_contratacion}\n"
            f"Código NIC: {self.codigo_contratacion}\n"
            f"Entidad: {self.entidad_contratante}\n"
            f"Provincia: {self.provincia}\n"
            f"Fecha Límite: {self.fecha_limite_propuesta or ''}\n"
            f"Contacto: {self.contacto or ''}\n"
            f"URL: {self.url_entidad or ''}\n"
        )
        lead_vals = {
            'name': f'[SERCOP] {self.objeto_contratacion[:200]}',
            'partner_id': partner.id if partner else False,
            'description': description,
            'team_id': team.id if team else False,
            'expected_revenue': self.valor_unitario * self.cantidad if self.valor_unitario and self.cantidad else 0,
            'type': 'opportunity',
        }
        lead = self.env['crm.lead'].create(lead_vals)
        self.write({
            'lead_id': lead.id,
            'lead_creado': True,
        })
        return lead

    def action_open_lead(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'res_id': self.lead_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_detalle(self):
        self.ensure_one()
        if self.url_entidad:
            return {
                'type': 'ir.actions.act_url',
                'url': self.url_entidad,
                'target': 'new',
            }
        return True

    @api.model
    def cron_importar_procesos(self):
        _logger.info('Inicio de importación SERCOP automática')
        imported = self.fetch_sercop_data()
        nuevos = self.search([('lead_creado', '=', False), ('es_tecnologia', '=', True)])
        lead_count = 0
        for proceso in nuevos:
            try:
                proceso._create_lead_from_proceso()
                lead_count += 1
            except Exception as e:
                _logger.error('Error creando lead para %s: %s', proceso.codigo_contratacion, str(e))
        _logger.info(
            'Importación SERCOP completada: %d procesos importados, %d leads creados',
            imported, lead_count,
        )
        return True
