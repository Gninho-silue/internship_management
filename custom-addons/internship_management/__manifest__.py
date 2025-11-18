# -*- coding: utf-8 -*-
{
    # Informations du module
    'name': 'Gestion des Stages TechPal',
    'version': '17.0.1.0.0',
    'category': 'Ressources Humaines',
    'summary': 'Système de gestion des stages pour TechPal Casablanca',

    'description': """
Système de Gestion des Stages - TechPal Casablanca
==================================================
Plateforme complète de gestion des stages incluant :
- Gestion des étudiants et encadrants
- Suivi des stages et progression
- Gestion documentaire et rapports
- Tableaux de bord personnalisés
- Notifications et alertes
    """,

    # Métadonnées
    'author': 'SILUE Stagiaire - TechPal Casablanca',
    'website': 'https://www.techpalservices.com/',
    'license': 'LGPL-3',
    'support': 'internship@techpal.ma',

    # Dépendances
    'depends': [
        'base',
        'mail',
        'contacts',
        'portal',
        'hr',
        'calendar',
    ],

    # Fichiers de données (ORDRE CRITIQUE!)
    'data': [
        # Security
        'security/internship_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/sequences.xml',
        'data/internship_cron.xml',
        'data/internship_meeting_mail_templates.xml',
        'data/internship_stage_mail_templates.xml',
        'data/mail_activity_type_data.xml',

        # Reports
        'reports/internship_report_templates.xml',
        'reports/internship_reports.xml',

        # Views (ORDRE CORRECT)
        'views/internship_presentation_views.xml',
        'views/internship_meeting_views.xml',
        'views/internship_stage_views.xml',  # ← AJOUTÉ
        'views/internship_account_views.xml',
        'views/internship_student_views.xml',
        'views/internship_supervisor_views.xml',
        'views/internship_area_views.xml',
        'views/internship_skill_views.xml',
        'views/internship_security_views.xml',
        'views/internship_document_views.xml',
        'views/internship_document_feedback_views.xml',
        'views/internship_todo_views.xml',
        'views/internship_dashboard_action.xml',  # ← NOUVEAU (OWL)

        # Menus
        'views/internship_menus.xml',
    ],

    # Assets (JavaScript/CSS)
    'assets': {
        'web.assets_backend': [
            'internship_management/static/src/dashboard/dashboard.js',
            'internship_management/static/src/dashboard/dashboard.xml',
            'internship_management/static/src/scss/dashboard.scss',  # ← CORRIGÉ
        ],
    },

    # Données de démonstration
    'demo': [
        # 'data/internship_demo_data.xml',
    ],

    # Paramètres techniques
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 15,

    # Dépendances externes Python
    'external_dependencies': {
        'python': ['python-dateutil', 'reportlab'],
    },

    # Images et captures d'écran
    'images': [
        'static/description/icon.png',
    ],

    # Tarification (Odoo Apps Store)
    'price': 0.00,
    'currency': 'EUR',

    # Informations de version
    'live_test_url': 'https://demo.techpal.ma/internship',
}
