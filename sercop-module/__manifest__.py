{
    'name': 'SERCOP - Compras Públicas CRM',
    'version': '17.0.1.0',
    'category': 'Sales/CRM',
    'summary': 'Importa necesidades de contratación de Compras Públicas y crea oportunidades CRM',
    'description': """
        Módulo que se conecta al portal de Compras Públicas (SERCOP) para importar
        necesidades de contratación relacionadas con tecnología (software, hosting,
        servidores, aplicaciones, etc.) y crear automáticamente oportunidades en CRM.

        Características:
        - Importación diaria automática mediante cron
        - Filtro por palabras clave configurables (software, hosting, servidor, etc.)
        - Creación automática de oportunidades en CRM
        - Importación manual desde wizard
        - Historial completo de procesos importados
    """,
    'author': 'Ecuabyte',
    'website': 'https://ecuabyte.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'crm',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'data/sercop_keyword_data.xml',
        'views/sercop_proceso_views.xml',
        'views/sercop_keyword_views.xml',
        'views/menu_views.xml',
        'views/sercop_import_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
