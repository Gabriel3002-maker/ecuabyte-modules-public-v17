from odoo import models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def website_form_input_filter(self, request, values):
        values = super().website_form_input_filter(request, values)
        if not values.get('name'):
            contact_name = values.get('contact_name', '')
            values['name'] = contact_name and "Contacto web: %s" % contact_name or "Contacto desde web"
        return values
