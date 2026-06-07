{
    'name': 'SERCOP - IA para Proformas',
    'version': '17.0.1.0',
    'category': 'Sales/CRM',
    'summary': 'Genera cotizaciones con IA desde procesos SERCOP',
    'description': '''
        Módulo que integra IA (Ollama/OpenAI) para analizar documentos
        de procesos SERCOP y generar cotizaciones profesionales en Odoo.
    ''',
    'depends': ['base', 'sercop-module', 'sale', 'crm', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/ai_provider_data.xml',
        'views/sercop_document_views.xml',
        'views/ai_provider_views.xml',
        'views/ai_quotation_wizard_views.xml',
        'views/sercop_proceso_views.xml',
        'views/crm_lead_views.xml',
        'views/menu_views.xml',
        'reports/sercop_quotation_report.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'external_dependencies': {
        'python': ['PyMuPDF'],
    },
}
