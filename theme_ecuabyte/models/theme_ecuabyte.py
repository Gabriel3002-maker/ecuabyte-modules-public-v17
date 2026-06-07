from odoo import models


class ThemeEcuabyte(models.AbstractModel):
    _inherit = 'theme.utils'

    def _theme_ecuabyte_post_copy(self, mod):
        self.enable_view('website.template_header_hamburger')
        self.enable_view('website.template_header_hamburger_align_right')
        self.enable_view('website.no_autohide_menu')

        self.disable_view('website.template_footer_contact')
        self.enable_view('theme_ecuabyte.ecuabyte_footer')
