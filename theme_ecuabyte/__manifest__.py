{
    'name': 'Ecuabyte Theme',
    'description': 'Ecuabyte Theme - Personalizada para Ecuador',
    'category': 'Theme/Services',
    'summary': 'Ecuabyte, Ecuador, Negocios, Servicios, Personalizado',
    'sequence': 150,
    'version': '1.0.0',
    'depends': ['theme_common', 'crm', 'website_crm'],
    'data': [
        'data/generate_primary_template.xml',
        'data/ir_asset.xml',
        'views/ecuabyte_header.xml',
        'views/ecuabyte_footer.xml',
        'views/ecuabyte_contactus.xml',
        'views/snippets/s_cover.xml',
        'views/snippets/s_features.xml',
        'views/snippets/s_text_image.xml',
        'views/new_page_template.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'images_preview_theme': {
        'website.s_cover_default_image': '/theme_ecuabyte/static/src/img/backgrounds/bg_cover.jpg',
        'website.s_text_image_default_image': '/theme_ecuabyte/static/src/img/content/image_content_01.jpg',
    },
    'configurator_snippets': {
        'homepage': ['s_cover', 's_text_image', 's_features'],
    },
    'license': 'LGPL-3',
    'assets': {
        'website.assets_editor': [
            'theme_ecuabyte/static/src/js/tour.js',
        ],
    },
}
