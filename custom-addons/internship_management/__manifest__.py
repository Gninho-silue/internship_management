# -*- coding: utf-8 -*-
{
    # Informations du module
    'name': 'Système de Gestion des Stages',
    'version': '17.0.1.0.0',
    'category': 'Ressources Humaines/Éducation',
    'summary': 'Plateforme complète de gestion des stages pour institutions éducatives',

    'description': """
Système de Gestion des Stages - Plateforme Professionnelle
===========================================================

Une solution complète pour la gestion des stages avec les fonctionnalités suivantes :

**Fonctionnalités principales :**
* Gestion complète du cycle de vie des stages
* Gestion des étudiants et encadrants
* Gestion documentaire avec génération automatique de PDF
* Suivi de progression avec tableaux Kanban
* Notifications et alertes automatiques

**Fonctionnalités avancées :**
* Système de sécurité basé sur les rôles
* Intégration email et templates
* Planification et gestion des réunions
* Tableau de bord et rapports analytiques
* Interface responsive mobile

**Utilisateurs cibles :**
* Institutions éducatives
* Départements RH d'entreprises
* Organismes de formation
* Coordinateurs de stages

Développé comme application professionnelle suivant les meilleures pratiques Odoo.
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

    # Reports
    'reports/defense_report_template.xml',
    'reports/convention_attestation_template.xml',
    'reports/evaluation_report_template.xml',
    'reports/stage_report_template.xml',
    'reports/internship_reports.xml',

    # Views (NOUVEL ORDRE!)
    'views/internship_presentation_views.xml',
    'views/internship_meeting_views.xml',        # ← DÉPLACER ICI (AVANT stage)
    'views/internship_stage_views.xml',          # ← APRÈS meeting
    'views/internship_student_views.xml',
    'views/internship_supervisor_views.xml',
    'views/internship_config_views.xml',
    'views/internship_security_views.xml',
    'views/internship_document_views.xml',
    'views/internship_communication_views.xml',
    'views/internship_document_feedback_views.xml',
    'views/internship_todo_views.xml',
    'views/internship_alert_views.xml',
    'views/internship_dashboard_views.xml',

    # Menus
    'views/internship_menus.xml',
],

    # Assets (JavaScript/CSS)
    'assets': {
        'web.assets_backend': [
            # Les assets OWL seront ajoutés ici
            # 'internship_management/static/src/dashboard/dashboard.js',
            # 'internship_management/static/src/dashboard/dashboard.xml',
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
        # 'static/description/banner.png',
        'static/description/icon.png',
    ],

    # Tarification (Odoo Apps Store)
    'price': 0.00,
    'currency': 'EUR',

    # Informations de version
    'live_test_url': 'https://demo.techpal.ma/internship',
}