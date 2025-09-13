{
    'name': 'Internship Management System',
    'version': '17.0.1.0.0',
    'category': 'Human Resources/Education',
    'summary': 'Complete internship management platform for educational institutions',
    'description': """
Internship Management System - Professional Platform
==================================================

A comprehensive solution for managing internships with the following features:

**Core Features:**
* Complete internship lifecycle management
* Student and supervisor management
* Document management with automated PDF generation
* Progress tracking with Kanban boards
* Automated notifications and alerts

**Advanced Features:**
* Role-based security system
* Email integration and templates
* Meeting scheduling and management
* Reporting and analytics dashboard
* Mobile-responsive interface

**Target Users:**
* Educational institutions
* Corporate HR departments  
* Training organizations
* Internship coordinators

Developed as a professional-grade application following Odoo best practices.
    """,
    'author': 'SILUE - Techpal Casablanca',
    'website': 'https://techpal.ma',
    'license': 'LGPL-3',
    'support': 'internship@techpal.ma',

    # Dependencies
    'depends': [
        'base',
        'mail',
        'contacts',
        'portal',
        'hr',
        'calendar',
    ],

    # Data files
    'data': [
        # Security (critical order!)
        'security/internship_security.xml',
        'security/ir.model.access.csv',

        # Base data
        'data/sequences.xml',
        'data/internship_language_data.xml',
        'data/internship_cron.xml',

        # Reports
        'reports/defense_report_template.xml',
        'reports/convention_attestation_template.xml',
        'reports/evaluation_report_template.xml',
        'reports/stage_report_template.xml',
        'reports/internship_reports.xml',

        # Views
        'views/internship_stage_views.xml',
        'views/internship_student_views.xml',
        'views/internship_supervisor_views.xml',
        'views/internship_config_views.xml',
        'views/internship_security_views.xml',
        'views/internship_document_views.xml',
        'views/internship_message_views.xml',
        'views/internship_notification_views.xml',
        'views/internship_meeting_views.xml',
        'views/internship_user_profile_views.xml',



        # Menus (last)
        'views/internship_menus.xml',
    ],

    # Assets 
    'assets': {
        'web.assets_backend': [
        ],
    },
    # Demo data
    'demo': [
        'data/internship_demo_data.xml',
    ],

    # Technical settings
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 15,

    # External dependencies
    'external_dependencies': {
        'python': ['python-dateutil', 'reportlab'],
    },

    # Images and screenshots
    'images': [
        'static/description/banner.png',
        'static/description/screenshot_dashboard.png',
        'static/description/screenshot_kanban.png',
    ],

    # Pricing (for Odoo Apps Store)
    'price': 0.00,
    'currency': 'EUR',

    # Version info
    'live_test_url': 'https://demo.techpal.ma/internship',
}