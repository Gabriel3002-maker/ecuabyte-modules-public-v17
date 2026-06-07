from odoo import models, fields


class SercopKeyword(models.Model):
    _name = 'sercop.keyword'
    _description = 'Palabra Clave SERCOP'
    _rec_name = 'name'
    _order = 'name'

    name = fields.Char(string='Palabra Clave', required=True, index=True)
    active = fields.Boolean(string='Activo', default=True)
    category = fields.Selection([
        ('software', 'Software'),
        ('hardware', 'Hardware'),
        ('infraestructura', 'Infraestructura'),
        ('servicios', 'Servicios TI'),
        ('dominios', 'Dominios/Hosting'),
        ('seguridad', 'Seguridad'),
    ], string='Categoría', default='software')
    note = fields.Text(string='Notas')
