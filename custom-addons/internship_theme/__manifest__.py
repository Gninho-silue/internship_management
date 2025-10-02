# -*- coding: utf-8 -*-
{
    'name': 'Internship Management - Theme',
    'version': '17.0.1.0.0',
    'category': 'Theme',
    'summary': 'Custom login design for Internship Management',
    'description': """
Theme Custom pour Gestion des Stages
=====================================
- Design login personnalisé
- Logo TechPal
- Couleurs corporate
    """,

    'author': 'SILUE - TechPal Casablanca',
    'website': 'https://www.techpalservices.com/',
    'license': 'LGPL-3',

    'depends': [
        'web',
        'internship_management',  # Dépendance du module principal
    ],

    'data': [
        'views/login_template.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            'internship_theme/static/src/scss/login.scss',
        ],
    },

    'installable': True,
    'application': False,
    'auto_install': False,
}